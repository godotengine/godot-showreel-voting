from flask import Blueprint, current_app, g, render_template, request

from gdshowreelvote.blueprints.forms import VOTE_ACTIONS, CastVoteForm, SelectVideoForm
from gdshowreelvote.database import DB, Showreel, ShowreelStatus, Video, Vote
from gdshowreelvote.utils import choose_random_video


bp = Blueprint('votes', __name__)


@bp.route('/')
def home():
	content = render_template('home.html')
	return render_template('default.html', content = content, user=g.user)


@bp.route('/about')
def about():
	content = render_template('about.html')
	return render_template('default.html', content = content)


@bp.route('/vote', methods=['GET'])
def vote_get():
	video = choose_random_video(g.user)
	# Is there any chance that there are multiple showreels in VOTE status?
	# Should we choose the showreel with a specific ID?
	
	total_video_count = DB.session.query(Video).count()
	total_user_votes = DB.session.query(Vote).filter(Vote.user_id == g.user.id).count()
	if video:
		data = {
			'id': video.id,
			'game': video.game,
			'author': video.author_name,
			'follow_me_link': video.follow_me_link,
			'video_link': video.video_link,
			'store_link': video.store_link,
		}
		# TODO: Need to make sure we extract the YouTube ID correctly
		youtube_id = video.video_link.split('v=')[-1]
		data['youtube_embed'] = f'https://www.youtube.com/embed/{youtube_id}'

	else:
		data = None
	progress = {
		'total': total_video_count, 
		'current': total_user_votes + 1,
	}
	
	content = render_template('vote.html', data=data, progress=progress, cast_vote_form=CastVoteForm(), select_specific_video_form=SelectVideoForm())
	return render_template('default.html', content = content, user=g.user)


@bp.route('/vote', methods=['POST'])
def vote():
	# Every time you visit this page, it should load a new entry
	# You should add an option argument allowing to load a specific entry to overwrite the vote
	cast_vote_form = CastVoteForm()
	select_specific_video_form = SelectVideoForm()
	skip_videos = []
	if cast_vote_form.validate():
		action = cast_vote_form.action.data
		video = DB.session.query(Video).filter(Video.id == cast_vote_form.video_id.data).first()
		if video:
			VOTE_ACTIONS[action](g.user, video)
		if action == 'skip':
			skip_videos.append(video.id)
		video = choose_random_video(g.user, skip_videos)
	elif select_specific_video_form.validate():
		video = DB.session.query(Video).filter(Video.id == select_specific_video_form.video_id.data).first()
		if not video:
			current_app.logger.warning(f"Video with ID {select_specific_video_form.video_id.data} not found.")
			return "Video not found", 404
	else:
		current_app.logger.warning(f"Form validation failed: {cast_vote_form.errors} {select_specific_video_form.errors}")
		return "Invalid form submission", 400

	total_video_count = DB.session.query(Video).count()
	total_user_votes = DB.session.query(Vote).filter(Vote.user_id == g.user.id).count()

	if video:
		data = {
			'id': video.id,
			'game': video.game,
			'author': video.author_name,
			'follow_me_link': video.follow_me_link,
			'video_link': video.video_link,
			'store_link': video.store_link,
		}
		# TODO: Need to make sure we extract the YouTube ID correctly
		youtube_id = video.video_link.split('v=')[-1]
		data['youtube_embed'] = f'https://www.youtube.com/embed/{youtube_id}'
	else:
		data = None
	progress = {
		'total': total_video_count, 
		'current': total_user_votes + 1,
	}

	return render_template('vote.html', data=data, progress=progress, cast_vote_form=cast_vote_form, select_specific_video_form=select_specific_video_form)


@bp.route('/history')
def history():
	progress = {
		'total': 310, # How many entries in total
		'current': 42, # How many entries has the user rated so far
	}
	content = render_template('history.html', progress=progress)
	return render_template('default.html', content = content)