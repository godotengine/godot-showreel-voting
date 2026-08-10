import csv
from io import StringIO

from flask import (
	Blueprint,
	Response,
	current_app,
	g,
	redirect,
	render_template,
	request,
	url_for,
)
from sqlalchemy import case, func, or_
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import NotFound

from gdshowreelvote import auth
from gdshowreelvote.blueprints.forms import (
	VOTE_ACTIONS,
	CastVoteForm,
	ManageShowreelsForm,
	SelectVideoForm,
	VideoSubmissionForm,
)
from gdshowreelvote.database import DB, Showreel, ShowreelStatus, User, Video, Vote
from gdshowreelvote.utils import (
	choose_random_video,
	extract_steam_app_id,
	get_total_votes_for_showreel,
	video_data,
	vote_data,
	voting_possible,
)

bp = Blueprint('votes', __name__)


@bp.route('/')
def home():
	active_submissions = DB.session.query(Showreel).filter(Showreel.status == ShowreelStatus.OPENED_TO_SUBMISSIONS).first()
	active_vote = DB.session.query(Showreel).filter(Showreel.status == ShowreelStatus.VOTE).first()
	content = render_template('home.html', user=g.user, active_submissions=active_submissions, active_vote=active_vote)
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
	if not voting_possible():
		return redirect(url_for('votes.home'))
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
	if not voting_possible():
		return redirect(url_for('votes.home'))
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
	if not voting_possible():
		return redirect(url_for('votes.home'))
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
	if not voting_possible():
		return redirect(url_for('votes.home'))
	limit = request.args.get('limit')
	page = int(request.args.get('page', 1))
	total_video_count = DB.session.query(Video).join(Showreel).filter(Showreel.status == ShowreelStatus.VOTE).count()
	total_user_votes = DB.session.query(Vote).join(Video).join(Showreel).filter(Showreel.status == ShowreelStatus.VOTE).filter(Vote.user_id == g.user.id).count()
	progress = {
		'total': total_video_count,
		'current': total_user_votes,
	}
	query = DB.session.query(Vote).join(Video).join(Showreel).filter(Showreel.status == ShowreelStatus.VOTE).filter(Vote.user_id == g.user.id).order_by(Vote.created_at.desc())

	if limit == 'all':
		total_results = query.count()
		per_page = total_results if total_results > 0 else 1
	else:
		per_page = 30
	
	try:
		submitted_votes = DB.paginate(query, page=page, per_page=per_page)
	except NotFound:
		submitted_votes = DB.paginate(query, page=1, per_page=per_page)


	#  We probably want to add pagination here
	content = render_template('history.html', progress=progress, submitted_votes=submitted_votes)

	if request.args.get('page') or request.args.get('limit'):
		return content
	return render_template('default.html', content = content, user=g.user)


@bp.route('/admin')
@auth.admin_required
def admin_view():
	form = ManageShowreelsForm()
	showreels = (
		DB.session.query(Showreel)
		.order_by(
			case(
				(Showreel.status == ShowreelStatus.VOTE, 0),
				(Showreel.status == ShowreelStatus.OPENED_TO_SUBMISSIONS, 1),
				else_=2))
		.all()
	)
	form.showreel_id.choices = [(showreel.id, showreel.title) for showreel in showreels]

	content = render_template('admin.html', form=form, showreels=showreels)
	if request.args.get('page'):
		return content
	return render_template('default.html', content = content, user=g.user)


@bp.route('/results')
@auth.admin_required
def download_vote_results():
	showreel_id = request.args.get("showreel_id", type=int)
	showreel = DB.session.get(Showreel, showreel_id)
	if showreel is None:
		return render_template('error.html', title="Showreel Not Found", message="No showreel ID provided.")
	result = (
        DB.session.query(
            Video,
            func.sum(case((Vote.rating == 1, 1), else_=0)).label("plus_votes"),
			func.sum(case((Vote.rating == -1, 1), else_=0)).label("minus_votes"),
			func.sum(case(((User.is_staff == True) & (Vote.rating != 0), 1), else_=0)).label("staff_votes"),
        	func.sum(case(((User.is_fund_member == True) & (Vote.rating != 0), 1), else_=0)).label("fund_member_votes")
		)
        .outerjoin(Vote, Vote.video_id == Video.id)
		.outerjoin(User, User.id == Vote.user_id)
		.filter(Video.showreel_id == showreel_id)
        .group_by(Video.id)
        .order_by(func.coalesce(func.sum(Vote.rating), 0).desc()).all()
    )

	csv_file = StringIO()
	writer = csv.writer(csv_file)
	writer.writerow(['Author', 'Follow-me link', 'Game', 'Video link', 'Download link', 'Contact email', 'Store Link', 'Steam App ID', 'Positive votes', 'Negative votes', 'staff', 'fund_member'])

	for video, plus_votes, minus_votes, staff_votes, fund_member_votes in result:
		writer.writerow([
            video.author_name,
            video.follow_me_link,
            video.game,
            video.video_link,
            video.video_download_link,
            video.contact_email,
            '\n'.join(video.store_link.split(';')),
			extract_steam_app_id(video.store_link),
            plus_votes,
            minus_votes,
			staff_votes,
			fund_member_votes
        ])
	response = Response(csv_file.getvalue(), mimetype='text/csv')
	response.headers["Content-Disposition"] = f"attachment; filename=vote_results_{showreel.title}.csv"
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


@bp.route('/submit', methods=['GET'])
def submit():
	active_showreel = DB.session.query(Showreel).filter(Showreel.status == ShowreelStatus.OPENED_TO_SUBMISSIONS).count()
	if active_showreel != 1:
		current_app.logger.warning("No active showreel or multiple active showreels found.")
		error_template = render_template('error.html', title="Submissions Closed", message="Submissions are currently closed.")
		return render_template('default.html', content = error_template, user=g.user)
	form = VideoSubmissionForm()
	content = render_template('submit.html', user=g.user, form=form)
	return render_template('default.html', content = content, user=g.user)


@bp.route('/submit', methods=['POST'])
@auth.login_required
def post_submit():
	formdata = request.form.copy()

	links = [
		formdata.get("store_link", "").strip(),
		formdata.get("store_link_2", "").strip(),
		formdata.get("store_link_3", "").strip(),
		formdata.get("store_link_4", "").strip(),
		formdata.get("store_link_5", "").strip(),
	]

	formdata["store_link"] = ";".join(link for link in links if link)

	form = VideoSubmissionForm(formdata)

	if not form.validate():
		return render_template('submit.html', user=g.user, form=form)
	
	active_showreel = DB.session.query(Showreel).filter(Showreel.status == ShowreelStatus.OPENED_TO_SUBMISSIONS).all()
	if not active_showreel or len(active_showreel) > 1:
		current_app.logger.warning("No active showreel or multiple active showreels found.")
		return render_template('error.html', title="Submissions Closed", message="Submissions are currently closed.")
	duplicate_video = DB.session.query(Video).filter(or_(Video.video_link == form.video_link.data, Video.video_download_link == form.video_download_link.data)).first()
	if duplicate_video:
		form.video_link.errors.append('A video with the same link or download link has already been submitted.')
		return render_template('submit.html', user=g.user, form=form)

	active_showreel = active_showreel[0]
	new_video = Video(
		game=form.game.data,
		author_name=form.author_name.data,
		contact_email=form.contact_email.data,
		video_link=form.video_link.data,
		video_download_link=form.video_download_link.data,
		follow_me_link=form.follow_me_link.data,
		store_link=form.store_link.data,
		author=g.user,
		showreel=active_showreel
		)
	try:
		DB.session.add(new_video)
		DB.session.commit()
	except IntegrityError as e:
		current_app.logger.error(f"Database integrity error while submitting video: {e}")
		DB.session.rollback()
		return render_template('submit.html', user=g.user, form=form)
	return render_template('home.html', user=g.user, active_submissions=True, submission_success=True)  # TODO: Add flag to show submission success message


@bp.route('/showreel/update-status', methods=['POST'])
@auth.admin_required
def update_showreel_status():
	form = ManageShowreelsForm()
	showreels = DB.session.query(Showreel).all()
	form.showreel_id.choices = [(showreel.id, showreel.title) for showreel in showreels]
	if not form.validate():
		return redirect(url_for('votes.admin_view'))
	showreel = DB.session.query(Showreel).filter(Showreel.id == form.showreel_id.data).first()
	if not showreel:
		return render_template('error.html', title="Showreel Not Found", message="The requested showreel was not found.")

	showreel.status = form.showreel_status.data
	DB.session.commit()
	return redirect(url_for('votes.admin_view'))


@bp.route('/user/submissions', methods=['GET'])
@auth.login_required
def user_submissions():
	open_showreel = DB.session.query(Showreel).filter(Showreel.status == ShowreelStatus.OPENED_TO_SUBMISSIONS).first()
	open_submissions = DB.session.query(Video).filter(Video.author_id == g.user.id).filter(Video.showreel == open_showreel).all()
	closed_submissions = DB.session.query(Video).filter(Video.author_id == g.user.id).filter(Video.showreel != open_showreel).all()
	
	content = render_template('user-submissions.html', user=g.user, open_submissions=open_submissions, closed_submissions=closed_submissions, open_showreel=open_showreel)
	if request.args.get('update'):
		return content
	return render_template('default.html', content = content, user=g.user)


@bp.route('/user/submissions/<int:video_id>/manage', methods=['GET'])
@auth.login_required
def manage_submission(video_id: int):
	video = DB.session.query(Video).filter(Video.id == video_id).filter(Video.author == g.user).first()

	if not video:
		return render_template('error.html', title="Video Not Found", message="The requested video submission was not found.")
	
	if video.showreel.status != ShowreelStatus.OPENED_TO_SUBMISSIONS:
		return render_template('error.html', title="Cannot Manage Submission", message="Submissions can only be managed while the showreel is open to submissions.")

	form = VideoSubmissionForm(obj=video)

	content = render_template('manage-submission.html', user=g.user, form=form, video_id=video.id)
	return render_template('default.html', content = content, user=g.user)


@bp.route('/user/submissions/<int:video_id>/delete', methods=['POST'])
@auth.login_required
def delete_submission(video_id: int):
	video = DB.session.query(Video).filter(Video.id == video_id).filter(Video.author == g.user).first()

	if not video:
		return render_template('error.html', title="Video Not Found", message="The requested video submission was not found.")
	
	if video.showreel.status != ShowreelStatus.OPENED_TO_SUBMISSIONS:
		return render_template('error.html', title="Cannot Delete Submission", message="Submissions can only be deleted while the showreel is open to submissions.")

	DB.session.delete(video)
	DB.session.commit()

	return redirect(url_for('votes.user_submissions'))


@bp.route('/user/submissions/<int:video_id>/update', methods=['POST'])
@auth.login_required
def update_submission(video_id: int):
	video = DB.session.query(Video).filter(Video.id == video_id).filter(Video.author == g.user).first()

	if not video:
		return render_template('error.html', title="Video Not Found", message="The requested video submission was not found.")
	
	if video.showreel.status != ShowreelStatus.OPENED_TO_SUBMISSIONS:
		return render_template('error.html', title="Cannot Update Submission", message="Submissions can only be updated while the showreel is open to submissions.")

	formdata = request.form.copy()
	
	links = [
		formdata.get("store_link", "").strip(),
		formdata.get("store_link_2", "").strip(),
		formdata.get("store_link_3", "").strip(),
		formdata.get("store_link_4", "").strip(),
		formdata.get("store_link_5", "").strip(),
	]

	formdata["store_link"] = ";".join(link for link in links if link)
	form = VideoSubmissionForm(formdata, obj=video)
	if not form.validate():
		return render_template('update-submissions.html', user=g.user, submissions=[video], open_showreel=video.showreel, form=form)

	video.game = form.game.data
	video.author_name = form.author_name.data
	video.contact_email = form.contact_email.data
	video.video_link = form.video_link.data
	video.video_download_link = form.video_download_link.data
	video.follow_me_link = form.follow_me_link.data
	video.store_link = form.store_link.data
	DB.session.commit()

	return redirect(url_for('votes.user_submissions', update='1'))


@bp.route("/showreel-results")
@auth.admin_required
def showreel_results():
	showreel_id = request.args.get("showreel_id", type=int)

	showreel = DB.session.get(Showreel, showreel_id)
	if not showreel:
		return render_template('error.html', title="Showreel Not Found", message="The requested showreel was not found.")

	vote_metrics = get_total_votes_for_showreel(showreel)

	return render_template("partials/vote-results.html", metrics=vote_metrics, showreel=showreel)
