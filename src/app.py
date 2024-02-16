# cas-sso-discord-bot

from typing import Optional, List

from cas import CASClient # https://github.com/Chise1/fastapi-cas-example
from fastapi import FastAPI, Depends, Request
from starlette.middleware.sessions import SessionMiddleware
#from starlette.requests import Request
#from starlette.responses import Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_discord import DiscordOAuthClient, RateLimited, Unauthorized # https://github.com/Tert0/fastapi-discord
from fastapi_discord import User as DiscordUser
#from fastapi_discord import Role as DiscordRole #???
from fastapi_discord import Guild as DiscordGuild
from fastapi_discord.exceptions import ClientSessionNotInitialized
from fastapi_discord.models import GuildPreview
#* OR ? :
#* from starlette_discord.client import DiscordOAuthClient # https://github.com/nwunderly/starlette-discord
import asyncio
from os import getenv
import logging
import platform

from httpx import AsyncClient

from .bot import Bot # TODO: 

from .models import User, UsersDB
from .database import engine, SessionLocal, Base
# test
Base.metadata.create_all(bind=engine)
def get_database_session():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

app = FastAPI(title=__name__)
app.mount("/static", StaticFiles(directory="static"), name="static")

cas_client = CASClient(
    version=getenv('CAS_VERSION', 1),
    service_url=getenv('CAS_SERVICE_URL'),
    server_url=getenv('CAS_SERVER_URL'),
)
app.add_middleware(SessionMiddleware, secret_key=getenv('SECRET'))

discord_auth = DiscordOAuthClient(
    client_id=getenv('DISCORD_CLIENT_ID'),
    client_secret=getenv('DISCORD_CLIENT_SECRET'),
    #redirect_url=getenv('DISCORD_REDIRECT_URL'),
    redirect_uri=str(getenv("SITE_URL", "http://localhost:8000"))+"/discord-callback",
    scopes=("identify")#, "guilds", "email") # scopes
)
DISCORD_TOKEN_URL = "https://discord.com/api/v10/oauth2/token" # ? https://github.com/Tert0/fastapi-discord/issues/96

#admin_guild: DiscordGuild = DiscordGuild(
#    id=getenv("ADMIN_GUILD_ID"),
#    name=getenv("ADMIN_GUILD_NAME", "Admin Guild"),
#    owner=???,
#    permissions=???
#)

templates = Jinja2Templates(directory="templates")

def env_var(key: str, default = None):
    value = getenv(key, default)
    if value is None:
        logging.error(f"In Jinja2Template env_var(key) filter: Environment variable with key={key} is not set")
        return ""
    return value

templates.env.filters["env_var"] = env_var


def addLoggingLevel(levelName: str, levelNum: int, methodName: str = None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
        raise AttributeError("{} already defined in logging module".format(levelName))
    if hasattr(logging, methodName):
        raise AttributeError("{} already defined in logging module".format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
        raise AttributeError("{} already defined in logger class".format(methodName))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)

    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)

@app.on_event("startup")
async def on_startup():
    await discord_auth.init()

@app.get('/teapot')
async def teapot():
    return HTMLResponse("<h1>This is a teapot 🫖</h1>", status_code=418)


@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(name="index.html", context={"request": request,"hello": "world"}
    )


@app.get('/user', response_class=HTMLResponse)
async def user(request: Request):
    print(request.session.get("user"))
    user = request.session.get("user")
    if user:
        if await discord_auth.isAuthenticated(request.session['access_token']):
            return templates.TemplateResponse(name="user_with_discord.html", context={"request": request,"cas_username": user, "discord_id": discord_auth.id, "discord_username": discord_auth.username})
        else:
            return HTMLResponse('Logged in as %s. <a href="/logout">Logout</a>' % user['user'])
    return HTMLResponse('Login required. <a href="/login">Login</a>', status_code=403)
    return RedirectResponse(request.url_for('login'))


@app.get('/login')
async def login(
    request: Request, next: Optional[str] = None,
    ticket: Optional[str] = None):
    if request.session.get("user", None):
        # Already logged in
        return RedirectResponse(request.url_for('user'))

    # next = request.args.get('next')
    # ticket = request.args.get('ticket')
    if not ticket:
        # No ticket, the request come from end user, send to CAS login
        cas_login_url = cas_client.get_login_url()
        print('CAS login URL: %s', cas_login_url)
        return RedirectResponse(cas_login_url)

    # There is a ticket, the request come from CAS as callback.
    # need call `verify_ticket()` to validate ticket and get user profile.
    print('ticket: %s', ticket)
    print('next: %s', next)

    user, attributes, pgtiou = await cas_client.verify_ticket(ticket)

    print(
        'CAS verify ticket response: user: %s, attributes: %s, pgtiou: %s',
        user, attributes, pgtiou)

    if not user:
        return HTMLResponse('Failed to verify ticket. <a href="/login">Login</a>')
    else:  # Login successfully, redirect according `next` query parameter.
        response = RedirectResponse(next)
        request.session['user'] = dict(user=user)
        return response


@app.get('/logout')
async def logout(request: Request):
    user = request.session.get("user")
    if user:
        redirect_url = request.url_for('logout_callback')
        cas_logout_url = cas_client.get_logout_url(redirect_url)
        print('CAS logout URL: %s', cas_logout_url)
        return RedirectResponse(cas_logout_url)
    else:
        return HTMLResponse('Not logged in. <a href="/login">Login</a>')
        return RedirectResponse(request.url_for('login'))


@app.get('/logout-callback')
def logout_callback(request: Request):
    # redirect from CAS logout request after CAS logout successfully
    # response.delete_cookie('username')
    request.session.pop("user", None)
    return HTMLResponse('Logged out from CAS. <a href="/login">Login</a>')
    return RedirectResponse(request.url_for('index'))


@app.get('/discord-login')
async def discord_login(request: Request):
    #TODO:
    #user_session_state = generate_random(seed=request.session.items())
    #session_state = randomASCII(len=12)
    #session_state = hashlib.sha256(os.urandom(1024)).hexdigest()
    return RedirectResponse(discord_auth.get_oauth_login_url(
        state="my_test_state" #TODO: generate state token ? based on user's session/request? see above commented
    )) # TODO: state https://discord.com/developers/docs/topics/oauth2#state-and-security
    return await discord_auth.login(request) # ?
    #return await RedirectResponse(discord_auth.oauth_login_url) # or discord_auth.get_oauth_login_url(state="my state")


@app.get('/discord-callback')
async def discord_callback(request: Request, code: str, state: str):
    cas_user = request.session.get("user")
    if cas_user:
        token, refresh_token = await discord_auth.get_access_token(code) # ?
        request.session['discord_refresh_token'] = refresh_token
        request.session['discord_token'] = await discord_auth.get_token() #! or just token from above ?

        user: DiscordUser = await discord_auth.user()
        request.session['discord_username'] = user.username+str(user.discriminator) # ?
        request.session["discord_global_name"] = user.global_name
        request.session["discord_id"] = user.id

        user_guilds: List[DiscordGuild] = await discord_auth.guilds()
        request.session["discord_guilds"] = user_guilds #TODO: check which guilds that the user and the bot are both in

        assert state == "my_test_state" # compares state for security # TODO: state
        
        return RedirectResponse(request.url_for('user'))
        #try:
        #    await discord_auth.callback(request)
        #    return RedirectResponse(request.url_for('user'))
        #except Unauthorized:
        #    return JSONResponse({"error": "Unauthorized"}, status_code=401)
        #except RateLimited:
        #    return JSONResponse({"error": "RateLimited"}, status_code=429)
        #except ClientSessionNotInitialized:
        #    return JSONResponse({"error": "ClientSessionNotInitialized"}, status_code=500)
    else:
        return RedirectResponse(request.url_for('login'))


#! needed ?
@app.get(
    "/authenticated",
    dependencies=[Depends(discord_auth.requires_authorization)],
    response_model=bool,
)
async def isAuthenticated(token: str = Depends(discord_auth.get_token)):
    try:
        auth = await discord_auth.isAuthenticated(token)
        return auth
    except Unauthorized:
        return False


@app.get('/discord-logout', dependencies=[Depends(discord_auth.requires_authorization)])
async def discord_logout(request: Request, token: str = Depends(discord_auth.get_token)):
    try:
        if await discord_auth.isAuthenticated(token):
    #if await discord_auth.isAuthenticated(request.session['access_token']):
            
            # TODO: sufficient ?

            #await discord_auth.revoke(request.session['discord_token']) #? not in fastapi-discord ?
            await revoke_discord_token(request.session['discord_token'], "access_token", request.session['discord_username'])

            request.session.pop("discord_token", None)
            request.session.pop("discord_refresh_token", None)
            request.session.pop('discord_username', None)
            request.session.pop("discord_global_name", None)
            request.session.pop("discord_id", None)
            request.session.pop("discord_guilds", None)

            return RedirectResponse(request.url_for('user'))
        else:
            return RedirectResponse(request.url_for('user'))
    except Unauthorized:
        cas_user = request.session.get("user")
        if cas_user:
            return RedirectResponse(request.url_for('user'))
        else:
            return RedirectResponse(request.url_for('login'))
        
async def revoke_discord_token(token: str, token_type: str=None, user: str=None):
    """
    Custom discord user token revoke implementation (which is missing from fastapi-discord).
    """
    async with AsyncClient(app=app, base_url=DISCORD_TOKEN_URL) as ac:
        response = await ac.post(
            "/revoke",
            data={"token": token, "token_type_hint": token_type},
            auth=(discord_auth.client_id, discord_auth.client_secret)
        )
        
    if response.status_code.OK:# or response.status_code == 200:
        logging.debug(f"revoke_discord_token: Discord token revoked successfully for {user}.")
        return True
    elif response.status_code == 401:
        logging.error(f"revoke_discord_token: 401 This AccessToken does not have the necessary scope.")
    elif response.status_code == 429:
        logging.error(f"revoke_discord_token: 429 You are being Rate Limited. Retry after: {response.json()['retry_after']}")
    else:
        logging.error(f"revoke_discord_token: Unexpected HTTP response {response.status_code}")
    return False


@app.exception_handler(Unauthorized)
async def unauthorized_error_handler(request: Request):
    error = "Unauthorized"
    return HTMLResponse(templates.TemplateResponse(name="401.html", context={"request": request,"error": error}), status_code=401)
    #return JSONResponse({"error": "Unauthorized"}, status_code=401)


@app.exception_handler(RateLimited)
async def rate_limit_error_handler(request: Request, e: RateLimited):
    return HTMLResponse(templates.TemplateResponse(name="429.html", context={"request": request,"retry_after": e.retry_after}), status_code=429)
    #return JSONResponse({"error": "RateLimited", "retry": e.retry_after, "message": e.message}, status_code=429)


@app.exception_handler(ClientSessionNotInitialized)
async def client_session_error_handler(request: Request, e: ClientSessionNotInitialized):
    print(e)
    return HTMLResponse(templates.TemplateResponse(name="500.html", context={"request": request,"error": e}), status_code=500)
    #return JSONResponse({"error": "Internal Error"}, status_code=500)


async def run_bot():

    addLoggingLevel("TRACE", logging.INFO - 5)

    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    consoleHandler.setLevel(logging.TRACE)
    rootLogger.addHandler(consoleHandler)

    if platform.system() == "Linux":
        fileInfoHandler = logging.handlers.RotatingFileHandler(
            filename="logs/info.log", mode="w", encoding="UTF-8", delay=True, backupCount=5
        )
        fileDebugHandler = logging.handlers.RotatingFileHandler(
            filename="logs/debug.log", mode="w", encoding="UTF-8", delay=True, backupCount=5
        )
        fileInfoHandler.setFormatter(logFormatter)
        fileInfoHandler.setLevel(logging.TRACE)
        fileInfoHandler.doRollover()
        rootLogger.addHandler(fileInfoHandler)
        fileDebugHandler.setFormatter(logFormatter)
        fileDebugHandler.setLevel(logging.DEBUG)
        fileDebugHandler.doRollover()
        rootLogger.addHandler(fileDebugHandler)

    else:
        logging.warning("Non Linux system. Log info and debug file won't be available.")

    bot = Bot(logger=rootLogger, logFormatter=logFormatter)
    #await bot.run(getenv("DISCORD_BOT_TOKEN"))

# ? needed ?
async def run_web():
    try:
        logging.debug("Run webapp")
        #await uvicorn.run(app, port=getenv('FASTAPI_PORT', 8000), host=getenv('FASTAPI_HOST', 'localhost')) # ?
    except:
        logging.debug("Webapp fail")
    
if __name__ == '__main__':
    import uvicorn

    #TODO: start Discord bot
    
    #if not getenv("BOT_DISABLED"):
    #    asyncio.create_task(run_bot()) # ? run Discord bot async

    uvicorn.run(app, port=getenv('FASTAPI_PORT', 8000), host=getenv('FASTAPI_HOST', 'localhost'))
    #asyncio.create_task(run_web()) # ? run FastAPI webapp async

