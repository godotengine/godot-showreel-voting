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

if __name__ == '__main__':
	app.run(debug=True)
