from datetime import timedelta
import hashlib
from http.client import HTTPException
from flask import Flask, g, render_template, session

from gdshowreelvote import auth
from gdshowreelvote.blueprints.votes import bp as votes_bp
from gdshowreelvote.database import DB, User, migrate

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
            if user := DB.session.get(User, oidc_info['sub']):
                g.user = user
            else:
                name = oidc_info.get('name', oidc_info.get('preferred_username', ''))
                g.user = User(id=oidc_info['sub'], name=name, email=oidc_info['email'])
                DB.session.add(g.user)
                DB.session.commit()
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


    # @app.cli.command('search-users')
    # @click.argument('name')
    # def search_users(name):
    #     for user in User.query.filter(User.name.like(f'%{name}%')).all():
    #         print(f'{user.name}, {user.email} (ID: {user.id})')


    # @app.cli.command('make-moderator')
    # @click.argument('user_id')
    # def make_moderator(user_id):
    #     user = User.query.get(user_id)
    #     user.moderator = True
    #     DB.session.commit()
    
    return app


app = create_app()


if __name__ == '__main__':
	app.run(debug=True)
