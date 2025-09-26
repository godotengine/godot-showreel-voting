import csv
from datetime import timedelta
import hashlib
from http.client import HTTPException
import os
import click
from flask import Flask, current_app, g, render_template, session

from gdshowreelvote import auth
from gdshowreelvote.blueprints.votes import bp as votes_bp
from gdshowreelvote.database import DB, Showreel, ShowreelStatus, User, Video, Vote, migrate

def create_app(config=None):
    # ------------------------------------------------
    # App Config
    # ------------------------------------------------
    app = Flask(__name__, instance_relative_config=True)

    # Load the default config
    app.config.from_pyfile('config.py', silent=True)
    
    app.config.from_mapping(
        SECRET_KEY = 'dev',
        SQLALCHEMY_DATABASE_URI = 'sqlite:///app.sqlite?charset=utf8mb4',
        OIDC_MOCK = True
    )
    if config:
        app.config.update(config)

    app.register_blueprint(votes_bp, url_prefix='/')

    DB.init_app(app)
    migrate.init_app(app, DB)
    auth.init_app(app)

    # ------------------------------------------------
    # OIDC User Handling
    # ------------------------------------------------
    # Set session timeout to 1 day
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

    @app.before_request
    def setup_globals():
        session.permanent = True
        oidc_info = session.get('user', None)

        if oidc_info:
            g.user = DB.session.get(User, oidc_info['sub'])
            # Calculate Gravatar hash
            g.user.gravatar_hash = hashlib.md5(g.user.email.encode('utf-8')).hexdigest()
        else:
            g.user = None

    # ------------------------------------------------
    # Error Handling
    # ------------------------------------------------
    @app.errorhandler(HTTPException)
    def page_not_found(error):
        user = g.user if hasattr(g, 'user') else None
        content = render_template('error.html', error=error)
        return render_template('default.html', content=content, user=user)
    

    # ------------------------------------------------
    # Commands
    # ------------------------------------------------

    @app.cli.command('create-sample-data')
    def create_sample_data():
        if current_app.config['ENV'] != 'dev':
            print('Sample data can only be created in development environment.')
            return
        print('Creating sample data...')
        # Reset state
        DB.session.query(Showreel).delete()
        DB.session.query(User).filter(User.email == 'author@example.com').delete()
        DB.session.query(Vote).delete()
        DB.session.query(Video).delete()
        DB.session.commit()
        # Create showreel
        showreel = Showreel(status=ShowreelStatus.VOTE, title='2025 Godot Desktop/Console Games')
        DB.session.add(showreel)
        DB.session.commit()
        # Create author of videos
        author = User(id='sample-author-id', email='author@example.com', username='Sample Author')
        DB.session.add(author)
        DB.session.commit()

        # Create sample video entries
        video_data = [{
            'game': 'Brotato',
            'author_name': 'Blobfish Games',
            'follow_me_link': 'https://twitter.com/BlobfishGames',
            'category': '2025 Godot Desktop/Console Games',
            'video_link': 'https://www.youtube.com/watch?v=nfceZHR7Yq0',
            'video_download_link': 'https://www.youtube.com/watch?v=nfceZHR7Yq0',
            'store_link': 'https://store.steampowered.com/app/1592190/Brotato/',
        },
        {'game': 'Vampire Survivors',
            'author_name': 'Blobfish Games',
            'follow_me_link': 'https://twitter.com/BlobfishGames',
            'category': '2025 Godot Desktop/Console Games',
            'video_link': 'https://www.youtube.com/watch?v=6HXNxWbRgsg',
            'video_download_link': 'https://www.youtube.com/watch?v=6HXNxWbRgsg',
            'store_link': 'https://store.steampowered.com/app/1592190/Brotato/',
        },
        ]
        for video in video_data:
            video = Video(game=video['game'],
                          author_name=video['author_name'],
                          follow_me_link=video['follow_me_link'],
                          video_link=video['video_link'],
                          video_download_link=video['video_download_link'],
                          store_link=video['store_link'],
                          author=author,
                          showreel=showreel)
            DB.session.add(video)
            DB.session.commit()

            print(f'Created sample video entry: {video.game} (ID: {video.id})')

        return showreel, author


    @app.cli.command('load-data-from-csv')
    @click.argument('file')
    def load_data_from_csv(file):
        showreel = DB.session.query(Showreel).first()
        author = DB.session.query(User).filter(User.id == 'sample-author-id').first()
        if not showreel or not author:
            print('No showreel or user to attach videos to. Please execute "uv run flask --app main create-sample-data" and then try again.')
            return

        file_path = 'instance/sample.csv'
        if file and os.path.isfile(file):
            file_path = file
        with open(file_path) as csvfile:
            spamreader = csv.DictReader(csvfile, delimiter=',')
            
            for row in spamreader:
                video = Video(game=row['Game'],
                          author_name=row['Author'],
                          follow_me_link=row['Follow-me link'],
                          video_link=row['Video link'],
                          video_download_link=row['Download link'],
                          store_link=row['Store Link'],
                          contact_email=row['Contact email'],
                          author=author,
                          showreel=showreel)
                DB.session.add(video)

            DB.session.commit()
            print(f'added {spamreader.line_num} videos')
    
    return app


app = create_app()


if __name__ == '__main__':
	app.run(debug=True)
