from flask import Blueprint, g, render_template


bp = Blueprint('board', __name__)


@bp.route('/')
def home():
	content = render_template('home.html')
	return render_template('default.html', content = content, user=g.user)


@bp.route('/about')
def about():
	content = render_template('about.html')
	return render_template('default.html', content = content)


@bp.route('/vote')
def vote():
	# Every time you visit this page, it should load a new entry
	# You should add an option argument allowing to load a specific entry to overwrite the vote
	
	data = { # I hardcoded an example for the entry:
		'game': 'Brotato',
		'author': 'Blobfish Games',
		'follow_me_link': 'https://twitter.com/BlobfishGames',
		'category': '2025 Godot Desktop/Console Games',
		'video_link': 'https://www.youtube.com/watch?v=nfceZHR7Yq0',
		'store_link': 'https://store.steampowered.com/app/1592190/Brotato/',
	}
	progress = {
		'total': 310, # How many entries in total
		'current': 42, # How many entries has the user rated so far
	}
	
	# TODO: Need to make sure we extract the YouTube ID correctly
	youtube_id = data['video_link'].split('v=')[-1]
	data['youtube_embed'] = f'https://www.youtube.com/embed/{youtube_id}'

	content = render_template('vote.html', data=data, progress=progress)
	return render_template('default.html', content = content)


@bp.route('/history')
def history():
	progress = {
		'total': 310, # How many entries in total
		'current': 42, # How many entries has the user rated so far
	}
	content = render_template('history.html', progress=progress)
	return render_template('default.html', content = content)