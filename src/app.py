# cas-sso-discord-bot

#! USE QUARK ??
#import quart.flask_patch
#from quart import Quart, request, sessions, redirect, url_for, render_template

from asgiref.wsgi import WsgiToAsgi # https://flask.palletsprojects.com/en/latest/deploying/asgi/

#! pip install "Flask[async]" # https://flask.palletsprojects.com/en/3.0.x/async-await/
from flask import Flask, request, session, redirect, url_for, render_template
import asyncio # https://testdriven.io/blog/flask-async/
# or use an WsgiToAsgi adapter: https://flask.palletsprojects.com/en/3.0.x/deploying/asgi/

from cas import CASClient, CASError # https://github.com/python-cas/python-cas
from flask_discord import DiscordOAuth2Session, requires_authorization, Unauthorized # https://github.com/weibeu/Flask-Discord
from os import getenv, environ

#app = Quart(__name__)
wsgi_app = Flask(__name__)
app = WsgiToAsgi(wsgi_app) # https://flask.palletsprojects.com/en/latest/deploying/asgi/
app.secret_key = getenv("APP_SECRET_KEY") # TODO: or generate at startup ?
environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true" if getenv("DEV_ENV") else "false" # !! Only in development environment (no https).

cas_client = CASClient(
    version=getenv("CAS_VERSION"),#3, # v2 or v1 ?
    service_url=getenv("CAS_SERVICE_URL"),
    server_url=getenv("CAS_SERVER_URL")
)

app.config["DISCORD_CLIENT_ID"] = getenv("DISCORD_CLIENT_ID")           # Discord client ID.
app.config["DISCORD_CLIENT_SECRET"] = getenv("DISCORD_CLIENT_SECRET")   # Discord client secret.
app.config["DISCORD_REDIRECT_URI"] = getenv("DISCORD_REDIRECT_URI")     # URL to your callback endpoint.
app.config["DISCORD_BOT_TOKEN"] = getenv("DISCORD_BOT_TOKEN")           # Required to access BOT resources.

discordAuth = DiscordOAuth2Session(app)

@app.route('/')
async def index():
    #return redirect(url_for("login"))
    return 'Hello! <a href="/login">CAS Login</a>'
    #return await render_template("index.html")


@app.route('/user')
async def user(method=['GET']):
    if 'username' in session:
        # Logged in with CAS
        if not discordAuth.authorized:
            # Not logged in with Discord
            return 'Logged in as %s. <a href="/logout">Logout</a>' % session['username']
        else:
            # Logged in with Discord
            return await render_template("user_with_discord.html", username=session['username'], discord_username=session['discord_username'])
    # Not logged in with CAS
    return 'Login required. <a href="/login">Login</a>', 403


@app.route('/login')
async def login():
    if 'username' in session:
        # Already logged in
        return redirect(url_for('user'))

    next = await request.args.get('next')
    ticket = await request.args.get('ticket')
    if not ticket:
        # No ticket, the request come from end user, send to CAS login
        cas_login_url = await cas_client.get_login_url()
        app.logger.debug('CAS login URL: %s', cas_login_url)
        return redirect(cas_login_url)

    # There is a ticket, the request come from CAS as callback.
    # need call `verify_ticket()` to validate ticket and get user profile.
    app.logger.debug('ticket: %s', ticket)
    app.logger.debug('next: %s', next)

    CASUser, attributes, pgtiou = await cas_client.verify_ticket(ticket)

    app.logger.debug(
        'CAS verify ticket response: user: %s, attributes: %s, pgtiou: %s', CASUser, attributes, pgtiou)

    if not CASUser:
        return 'Failed to verify ticket. <a href="/login">Login</a>'
    else:  # Login successfully, redirect according `next` query parameter.
        session['username'] = CASUser
        return redirect(next)

@app.route('/discord-login')
async def discord_login():
    if 'username' in session:
        # Already logged in
        # TODO: Discord OAuth login
        return await discordAuth.create_session()
    else:
        return redirect(url_for('login'))
    
@app.route("/discord-callback")
async def discord_callback():
    data = await discordAuth.callback()

    app.logger.debug(data)
    if getenv("DEBUG"):
        print(data)

    discordUser = await discordAuth.fetch_user()
    session['discord_id'] = discordUser.id
    session['discord_username'] = discordUser.name
    session['discord_discriminator'] = discordUser.discriminator
    #session['discord_global_name'] = discordUser.globalName

    # User is logged in with CAS and Discord
    await link_accounts(session['username'], session['discord_id'])
    # Give role to Discord user
    await give_role(session['discord_id'])

    return redirect(url_for("user"))

#? needed ?
@app.errorhandler(Unauthorized)
async def redirect_unauthorized(e):
    app.logger.info("Unauthorized request: %s", e)
    print("Unauthorized request: ", e)
    return redirect(url_for("login"))

@app.route('/discord-logout')
async def discord_logout():
    await discordAuth.revoke() # Discord logout
    return redirect(url_for("user"))

@app.route('/unlink-discord')
async def unlink_discord():
    if 'username' in session and discordAuth.authorized:
        #await 
        pass
        await unlink_discord(session['username'], session['discord_id'])
        return redirect(url_for("user"))
    else:
        return redirect(url_for("login"))

@app.route('/logout')
async def logout():
    await discordAuth.revoke() # Discord logout

    redirect_url = url_for('logout_callback', _external=True)
    cas_logout_url = await cas_client.get_logout_url(redirect_url)
    app.logger.debug('CAS logout URL: %s', cas_logout_url)

    return redirect(cas_logout_url) # CAS logout


@app.route('/logout_callback')
async def logout_callback():
    # redirect from CAS logout request after CAS logout successfully
    session.pop('username', None)
    #return 'Logged out from CAS. <a href="/login">Login</a>'
    return await redirect(url_for('index'))

async def link_accounts(cas_username, discord_id):
    #await 
    pass # TODO: add to database

async def unlink_discord(cas_username, discord_id):
    #await 
    pass # TODO: remove discord_id entry from database for this user

async def give_role(discord_id):
    #await 
    pass # TODO: give role to Discord user


if __name__ == '__main__':

    # generate app secret key if not set
    if not app.secret_key:
        from os import urandom
        app.secret_key = urandom(24)

    #TODO: run discord bot
    
    #TODO: run webserver from different thread

    #app.run(debug=True)
    app.run(debug=True if getenv("DEBUG") else False)