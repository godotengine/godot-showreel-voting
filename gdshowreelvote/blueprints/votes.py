import csv
from io import StringIO
from sqlalchemy import case, func
from werkzeug.exceptions import NotFound

from flask import Blueprint, Response, current_app, g, redirect, render_template, request, url_for

from gdshowreelvote import auth
from gdshowreelvote.blueprints.forms import VOTE_ACTIONS, CastVoteForm, SelectVideoForm
from gdshowreelvote.database import DB, User, Video, Vote
from gdshowreelvote.utils import choose_random_video, get_total_votes, video_data, vote_data


bp = Blueprint('votes', __name__)


@bp.route('/')
def home():
	content = render_template('home.html', user=g.user)
	return render_template('default.html', content = content, user=g.user)


@bp.route('/about')
def about():
	content = render_template('about.html')
	return render_template('default.html', content = content, user=g.user)


@bp.route('/before-you-vote')
def before_you_vote():
	content = render_template('before-you-vote.html')
	return render_template('default.html', content = content, user=g.user)


@bp.route('/vote', methods=['GET'])
@bp.route('/vote/<int:video_id>', methods=['GET'])
@auth.vote_role_required
def vote_get(video_id=None):
	if video_id:
		video = DB.session.query(Video).filter(Video.id == video_id).first()
		if not video:
			current_app.logger.warning(f"Video with ID {video_id} not found.")
			return "Video not found", 404
	else:
		video = choose_random_video(g.user)

	data, progress = vote_data(g.user, video)
	
	content = render_template('vote.html', data=data, progress=progress, cast_vote_form=CastVoteForm(), select_specific_video_form=SelectVideoForm())
	return render_template('default.html', content = content, user=g.user, hide_nav=True)


@bp.route('/vote', methods=['POST'])
@auth.vote_role_required
def vote():
	cast_vote_form = CastVoteForm()
	select_specific_video_form = SelectVideoForm()
	if cast_vote_form.validate():
		action = cast_vote_form.action.data
		video = DB.session.query(Video).filter(Video.id == cast_vote_form.video_id.data).first()
		if not video:
			current_app.logger.warning(f"Video with ID {cast_vote_form.video_id.data} not found.")
			return "Video not found", 404
		VOTE_ACTIONS[action](g.user, video)
	else:
		current_app.logger.warning(f"Form validation failed: {cast_vote_form.errors} {select_specific_video_form.errors}")
		return "Invalid form submission", 400

	video = choose_random_video(g.user)
	data, progress = vote_data(g.user, video)

	return render_template('vote.html', data=data, progress=progress, cast_vote_form=cast_vote_form, select_specific_video_form=select_specific_video_form)


@bp.route('/vote/<int:video_id>/delete', methods=['POST'])
@auth.vote_role_required
def delete_vote(video_id: int):
	vote = DB.session.query(Vote).filter(Vote.user_id == g.user.id).filter(Vote.video_id == video_id).first()
	if not vote:
		current_app.logger.warning(f"Video with ID {video_id} not found.")
		return "Video not found", 404

	DB.session.delete(vote)
	DB.session.commit()

	return redirect(url_for('votes.history'))


@bp.route('/history')
@auth.vote_role_required
def history():
	page = int(request.args.get('page', 1))
	total_video_count = DB.session.query(Video).count()
	total_user_votes = DB.session.query(Vote).filter(Vote.user_id == g.user.id).count()
	progress = {
		'total': total_video_count,
		'current': total_user_votes,
	}
	query = DB.session.query(Vote).filter(Vote.user_id == g.user.id).order_by(Vote.created_at.desc())

	try:
		submitted_votes = DB.paginate(query, page=page, per_page=30)
	except NotFound:
		submitted_votes = DB.paginate(query, page=1, per_page=30)


	#  We probably want to add pagination here
	content = render_template('history.html', progress=progress, submitted_votes=submitted_votes)
	if request.args.get('page'):
		return content
	return render_template('default.html', content = content, user=g.user)


@bp.route('/admin')
@auth.admin_required
def admin_view():
	total_votes, positive_votes, vote_tally = get_total_votes()

	content = render_template('admin.html', vote_tally=vote_tally, total_votes=total_votes, positive_votes=positive_votes)
	if request.args.get('page'):
		return content
	return render_template('default.html', content = content, user=g.user)


@bp.route('/results')
@auth.admin_required
def download_vote_results():
	result = (
        DB.session.query(
            Video,
            func.sum(case((Vote.rating == 1, 1), else_=0)).label("plus_votes"),
			func.sum(case((Vote.rating == -1, 1), else_=0)).label("minus_votes"),
			func.sum(case((User.is_staff == True, 1), else_=0)).label("staff_votes"),
			func.sum(case((User.is_fund_member == True, 1), else_=0)).label("fund_member_votes"),
        )
        .outerjoin(Vote, Vote.video_id == Video.id)
		.outerjoin(User, User.id == Vote.user_id)
        .group_by(Video.id)
        .order_by(func.coalesce(func.sum(Vote.rating), 0).desc()).all()
    )

	csv_file = StringIO()
	writer = csv.writer(csv_file)
	writer.writerow(['Author', 'Follow-me link', 'Game', 'Video link', 'Download link', 'Contact email', 'Store Link', 'Positive votes', 'Negative votes', 'staff', 'fund_member'])

	for video, plus_votes, minus_votes, staff_votes, fund_member_votes in result:
		writer.writerow([
            video.author_name,
            video.follow_me_link,
            video.game,
            video.video_link,
            video.video_download_link,
            video.contact_email,
            video.store_link,
            plus_votes,
            minus_votes,
			staff_votes,
			fund_member_votes
        ])
	response = Response(csv_file.getvalue(), mimetype='text/csv')
	response.headers["Content-Disposition"] = "attachment; filename=vote_results.csv"
	return response


@bp.route('/view/<int:video_id>', methods=['GET'])
def video_view(video_id: int):
	video = DB.session.query(Video).filter(Video.id == video_id).first()
	if not video:
		current_app.logger.warning(f"Video with ID {video_id} not found.")
		return "Video not found", 404

	data = video_data(video)
	content = render_template('video-view.html', data=data)
	return render_template('default.html', content = content, user=g.user, hide_nav=True)
