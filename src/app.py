from flask import Flask, request, session, redirect, url_for
from cas import CASClient, CASError # https://github.com/python-cas/python-cas
from os import getenv

app = Flask(__name__)
app.secret_key = getenv("APP_SECRET_KEY") # TODO: or generate at startup ?

cas_client = CASClient(
    version=getenv("CAS_VERSION"),#3, # v2 or v1 ?
    service_url=getenv("CAS_SERVICE_URL"),
    server_url=getenv("CAS_SERVER_URL")
)


@app.route('/')
def index():
    #return redirect(url_for('login'))
    return 'Hello! <a href="/login">CAS Login</a>'


@app.route('/user')
def user(method=['GET']):
    if 'username' in session:
        return 'Logged in as %s. <a href="/logout">Logout</a>' % session['username']
    return 'Login required. <a href="/login">Login</a>', 403


@app.route('/login')
def login():
    if 'username' in session:
        # Already logged in
        return redirect(url_for('user'))

    next = request.args.get('next')
    ticket = request.args.get('ticket')
    if not ticket:
        # No ticket, the request come from end user, send to CAS login
        cas_login_url = cas_client.get_login_url()
        app.logger.debug('CAS login URL: %s', cas_login_url)
        return redirect(cas_login_url)

    # There is a ticket, the request come from CAS as callback.
    # need call `verify_ticket()` to validate ticket and get user profile.
    app.logger.debug('ticket: %s', ticket)
    app.logger.debug('next: %s', next)

    user, attributes, pgtiou = cas_client.verify_ticket(ticket)

    app.logger.debug(
        'CAS verify ticket response: user: %s, attributes: %s, pgtiou: %s', user, attributes, pgtiou)

    if not user:
        return 'Failed to verify ticket. <a href="/login">Login</a>'
    else:  # Login successfully, redirect according `next` query parameter.
        session['username'] = user
        return redirect(next)


@app.route('/logout')
def logout():
    redirect_url = url_for('logout_callback', _external=True)
    cas_logout_url = cas_client.get_logout_url(redirect_url)
    app.logger.debug('CAS logout URL: %s', cas_logout_url)

    return redirect(cas_logout_url)


@app.route('/logout_callback')
def logout_callback():
    # redirect from CAS logout request after CAS logout successfully
    session.pop('username', None)
    #return 'Logged out from CAS. <a href="/login">Login</a>'
    return redirect(url_for('index'))
