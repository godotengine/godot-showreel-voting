from werkzeug.exceptions import NotFound

from flask import Blueprint, current_app, g, render_template, request

from gdshowreelvote import auth
from gdshowreelvote.blueprints.forms import VOTE_ACTIONS, CastVoteForm, SelectVideoForm
from gdshowreelvote.database import DB, Video, Vote
from gdshowreelvote.utils import choose_random_video, get_total_votes, vote_data


bp = Blueprint('votes', __name__)


@bp.route('/')
def home():
	content = render_template('home.html')
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
@auth.login_required
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
	return render_template('default.html', content = content, user=g.user)


@bp.route('/vote', methods=['POST'])
@auth.login_required
def vote():
	cast_vote_form = CastVoteForm()
	select_specific_video_form = SelectVideoForm()
	skip_videos = []
	if cast_vote_form.validate():
		action = cast_vote_form.action.data
		video = DB.session.query(Video).filter(Video.id == cast_vote_form.video_id.data).first()
		if not video:
			current_app.logger.warning(f"Video with ID {cast_vote_form.video_id.data} not found.")
			return "Video not found", 404
		VOTE_ACTIONS[action](g.user, video)
		if action == 'skip':
			skip_videos.append(video.id)
	else:
		current_app.logger.warning(f"Form validation failed: {cast_vote_form.errors} {select_specific_video_form.errors}")
		return "Invalid form submission", 400

	video = choose_random_video(g.user, skip_videos)
	data, progress = vote_data(g.user, video)

	return render_template('vote.html', data=data, progress=progress, cast_vote_form=cast_vote_form, select_specific_video_form=select_specific_video_form)


@bp.route('/history')
@auth.login_required
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
	page = int(request.args.get('page', 1))
	vote_tally = get_total_votes(page)

	content = render_template('admin.html', vote_tally=vote_tally)
	if request.args.get('page'):
		return content
	return render_template('default.html', content = content, user=g.user)