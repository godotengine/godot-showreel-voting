from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
	content = render_template('home.html')
	return render_template('default.html', content = content)

@app.route('/about')
def about():
	content = render_template('about.html')
	return render_template('default.html', content = content)

@app.route('/vote')
def vote():
	data = {
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


@app.route('/history')
def history():
	content = render_template('history.html')
	return render_template('default.html', content = content)

if __name__ == '__main__':
	app.run(debug=True)
