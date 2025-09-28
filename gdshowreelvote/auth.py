from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List
from flask import Flask, current_app, render_template, request, url_for, session
from flask import redirect
from authlib.integrations.flask_client import OAuth

from gdshowreelvote.database import User, DB

ADMIN_ROLE = 'admin'
STAFF_ROLE = 'staff'

oauth = OAuth()

MOCK_USERS = {
    'moderator': {'mod': True, 'staff': True, 'fund_member': True},
    'staff': {'mod': False, 'staff': True, 'fund_member': False},
    'diamond-member': {'mod': False, 'staff': False, 'fund_member': True},
    'user': {'mod': False, 'staff': False, 'fund_member': False},
}


def login_required(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if session.get('user'):
            return f(*args, **kwargs)
        else:
            return redirect(url_for('oidc.login'))
    return decorated_func


def admin_required(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if session.get('user') and ADMIN_ROLE in session['user'].get('roles', []):
            return f(*args, **kwargs)
        else:
            return redirect(url_for('oidc.login'))
    return decorated_func


def _can_vote(user: Dict) -> bool:
    if ADMIN_ROLE in user.get('roles', []) or STAFF_ROLE in user.get('roles', []) or _fund_member_can_vote(user):
        return True
    return False
    

def vote_role_required(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if session.get('user') and _can_vote(session['user']):
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
    roles = []
    roles.append(ADMIN_ROLE) if MOCK_USERS[username]['mod'] else None
    roles.append(STAFF_ROLE) if MOCK_USERS[username]['staff'] else None
    fund_roles = []
    fund_roles.append('tier-diamond') if MOCK_USERS[username]['fund_member'] else None
    oidc_info = {
        'sub': f'MOCK_USER:{username}',
        'email_verified': True,
        'name': username.capitalize(),
        'preferred_username': username,
        'given_name': username.capitalize(),
        'family_name': username.capitalize(),
        'email': f'{username}@example.com',
        'roles': roles,
        'fund': {'roles': fund_roles}
    }
    user = DB.session.get(User, oidc_info['sub'])
    if not user:
        user = User(id=oidc_info['sub'], username=oidc_info['name'], email=oidc_info['email'], 
                    is_staff=STAFF_ROLE in oidc_info['roles'] or _fund_member_can_vote(oidc_info), 
                    is_superuser=ADMIN_ROLE in oidc_info['roles'])
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


def _fund_member_can_vote(user: Dict):
    fund_roles = user.get('fund', {}).get('roles', [])
    return any([role in fund_roles for role in current_app.config.get('FUND_ROLES_WITH_VOTE_RIGHTS', [])])


def oidc_auth():
    token = oauth.oidc.authorize_access_token()
    session['user'] = token['userinfo']
    if user := DB.session.get(User, token['userinfo']['sub']):
        user.is_staff = STAFF_ROLE in session['user'].get('roles', []) or _fund_member_can_vote(session['user'])
        user.is_superuser = ADMIN_ROLE in session['user'].get('roles', [])
    else:
        user = User(
            id=token['userinfo']['sub'],
            username=token['userinfo'].get('name', token['userinfo'].get('preferred_username', '')),
            email=token['userinfo']['email'],
            is_staff = STAFF_ROLE in session['user'].get('roles', []) or _fund_member_can_vote(session['user']),
            is_superuser = ADMIN_ROLE in session['user'].get('roles', []),
        )
        DB.session.add(user)
    DB.session.commit()
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
