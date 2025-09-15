from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, current_app, render_template, request, url_for, session
from flask import redirect
from authlib.integrations.flask_client import OAuth

from gdshowreelvote.database import User, DB


oauth = OAuth()

MOCK_USERS = {
    # Key: username, Value: moderator permission
    'moderator': {'mod': True, 'sub': True},
    'subscriber': {'mod': False, 'sub': True},
    'user': {'mod': False, 'sub': False},
}


def login_required(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if session.get('user'):
            return f(*args, **kwargs)
        else:
            return redirect(url_for('oidc.login'))
    return decorated_func


def get_issuer():
    if current_app.config.get('OIDC_MOCK', False):
        return 'https://example.org/keycloak/realms/test'
    else:
        return oauth.oidc.load_server_metadata()['issuer']


# Mock implementation

def mock_login():
    content = render_template('mock-login.html', users=MOCK_USERS)
    return render_template('default.html', content=content, title='Login')


def mock_auth():
    username = request.form.get('username', '').lower()
    if not username in MOCK_USERS:
        return redirect(url_for('oidc.login'))
    moderator = MOCK_USERS[username]['mod']
    oidc_info = {
        'sub': f'MOCK_USER:{username}',
        'email_verified': True,
        'name': username.capitalize(),
        'preferred_username': username,
        'given_name': username.capitalize(),
        'family_name': username.capitalize(),
        'email': f'{username}@example.com'
    }
    user = DB.session.get(User, oidc_info['sub'])
    if not user:
        user = User(id=oidc_info['sub'], username=oidc_info['name'], email=oidc_info['email'], is_staff=moderator)
        DB.session.add(user)
        DB.session.commit()
    

    session['user'] = oidc_info
    return redirect('/')


def mock_logout():
    session.pop('user', None)
    return redirect('/')


# OIDC implementation

def oidc_login():
    redirect_uri = url_for('oidc.auth', _external=True)
    return oauth.oidc.authorize_redirect(redirect_uri)


def oidc_auth():
    token = oauth.oidc.authorize_access_token()
    session['user'] = token['userinfo']
    return redirect('/')


def oidc_logout():
    session.pop('user', None)
    return redirect('/')


def init_app(app: Flask):
    if app.config.get('OIDC_MOCK', False):
        app.add_url_rule('/login', 'oidc.login', mock_login)
        app.add_url_rule('/auth', 'oidc.auth', mock_auth, methods=['POST'])
        app.add_url_rule('/logout', 'oidc.logout', mock_logout)
    else:
        oauth.init_app(app)
        oauth.register(name='oidc')
        app.add_url_rule('/login', 'oidc.login', oidc_login)
        app.add_url_rule('/auth', 'oidc.auth', oidc_auth)
        app.add_url_rule('/logout', 'oidc.logout', oidc_logout)
