# cas-sso-discord-bot

from os import getenv
from dotenv import load_dotenv
load_dotenv()

from typing import Optional, List

from cas import CASClient # https://github.com/Chise1/fastapi-cas-example # python_cas ?
from fastapi import FastAPI, Depends, Request
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_discord import DiscordOAuthClient, RateLimited, Unauthorized # https://github.com/Tert0/fastapi-discord
#* OR ? :
#* from starlette_discord.client import DiscordOAuthClient # https://github.com/nwunderly/starlette-discord
from fastapi_discord import User as DiscordUser
#from fastapi_discord import Role as DiscordRole #?
from fastapi_discord import Guild as DiscordGuild
from fastapi_discord.exceptions import ClientSessionNotInitialized
from fastapi_discord.models import GuildPreview
import asyncio
import logging
import platform
from time import time
from httpx import AsyncClient

from bot import Bot # TODO: implement bot
from locales import Locale, DEFAULT_LANG

# ------------


VERSION = "2.0.0-alpha.2"


# ------------

DEBUG=True if getenv("DEBUG") is not None or getenv("DEBUG") != "" else False

logger = logging.getLogger("app")

#locale: Locale = Locale(debug=DEBUG)

def init():
    if DEBUG:
        #logging.basicConfig(level=logging.DEBUG)
        logging.basicConfig(
            level=logging.DEBUG,
            format="{asctime} [{threadName}] ({filename}:{lineno}) [{levelname}]  {message}", # [{threadName}]
            style="{",
            datefmt="%Y-%m-%d %H:%M"
        )
        logger.info("Debug mode enabled")
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="{asctime} [{filename}:{lineno}-{levelname}]  {message}", # [{threadName}]
            style="{",
            datefmt="%Y-%m-%d %H:%M"
        )

    logger.info("### Launching app...")
    logger.info("###------------------------")
    logger.info("### Name: "+str(getenv("APP_NAME")))
    logger.info("### Version: "+str(VERSION))
    logger.info("###------------------------")
    # ------ init() end ------

#from models import User, UsersDB #?
#from database import engine, SessionLocal, Base
# test
#Base.metadata.create_all(bind=engine)
#def get_database_session():
#    try:
#        db = SessionLocal()
#        yield db
#    finally:
#        db.close()

#description = f"""
#{app.locale.lang_str('main_description', DEFAULT_LANG)}
#
#_Uses CAS-SSO-Discord-Bot: [github.com/LucasPlacentino/cas-sso-discord-bot](https://github.com/LucasPlacentino/cas-sso-discord-bot)_
#"""

#LOCALE: Locale = Locale(debug=DEBUG)

class App(FastAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.locale: Locale = None # extends FastAPI with locale

# FastAPI App
#app = FastAPI(
app = App(
    title=getenv("APP_NAME"),
    description=getenv("APP_DESCRIPTION"),
    version=VERSION,
    openapi_url=None,
    docs_url=None,
    redoc_url=None
)
app.mount("/static", StaticFiles(directory="static"), name="static")

# CAS Client
cas_client = CASClient(
    version=getenv('CAS_VERSION', 1),
    #service_url=getenv('CAS_SERVICE_URL', "http://localhost:8000/login"),
    service_url=str(getenv('SITE_URL', "http://localhost:8000"))+"/login",
    server_url=getenv('CAS_SERVER_URL'),
    #validate_url=getenv('CAS_VALIDATE_URL', "/serviceValidate"),
)
CAS_VALIDATE_PATH = getenv('CAS_VALIDATE_PATH', "/serviceValidate") # or "/proxyValidate" ?

# Session Middleware for FastAPI
APP_SECRET_KEY = getenv('APP_SECRET_KEY')
if APP_SECRET_KEY is None:
    logger.error("APP_SECRET_KEY not set")
    exit(1)
app.add_middleware(SessionMiddleware, # https://www.starlette.io/middleware/#sessionmiddleware
                    secret_key=APP_SECRET_KEY,
                    max_age=int(getenv('SESSION_MAX_AGE',12*3600)), # 12*1 hour. Session expiry time in seconds. Defaults to 2 weeks. If set to None then the cookie will last as long as the browser session
                    same_site="strict", # flag prevents the browser from sending session cookie along with cross-site requests, default:"lax" or "strict"
                    https_only=False, # indicate that Secure flag should be set (can be used with HTTPS only), default:False
                    )

# Discord OAuth Client
discord_auth = DiscordOAuthClient(
    client_id=getenv('DISCORD_CLIENT_ID'),
    client_secret=getenv('DISCORD_CLIENT_SECRET'),
    #redirect_url=getenv('DISCORD_REDIRECT_URI'),
    redirect_uri=str(getenv("SITE_URL", "http://localhost:8000"))+"/discord-callback",
    scopes=("identify","guilds")#, "guilds", "email") # scopes default: just "identify"
)
logger.info(f"discord_auth scopes: {discord_auth.scopes.replace('%20', '_')}")
DISCORD_TOKEN_URL = "https://discord.com/api/v10/oauth2/token" # ? https://github.com/Tert0/fastapi-discord/issues/96
#DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token" # no version in url ?

#admin_guild: DiscordGuild = DiscordGuild(
#    id=getenv("ADMIN_GUILD_ID"),
#    name=getenv("ADMIN_GUILD_NAME", "Admin Guild"),
#    owner=???,
#    permissions=???
#)


templates = Jinja2Templates(directory="templates")

def env_var(key: str, default: Optional[str] = None):
    value = getenv(key, default)
    if value is None:
        logger.error(f"In Jinja2Template env_var(key) filter: Environment variable with key={key} is not set")
        return ""
    return value

def is_debug() -> bool:
    return DEBUG

# Provide Python functions inside Jinja templates :
templates.env.globals.update(env_var=env_var) # or templates.env.filter["env_var"] ?
#templates.env.globals.update(lang_str=app.locale.lang_str) # get string from language file
templates.env.globals.update(time=time) # get current time
templates.env.globals.update(is_debug=is_debug) # check if in debug mode


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
    logger.info("Starting up...")
    await discord_auth.init()
    app.locale = Locale(debug=DEBUG)
    templates.env.globals.update(lang_str=app.locale.lang_str) # get string from language file



@app.get('/teapot')
async def teapot():
    return HTMLResponse("<h1>This is a teapot 🫖</h1>", status_code=418)
@app.get('/hello')
async def hello():
    return HTMLResponse("<h1>Hello, world!</h1>")

@app.get('/', response_class=RedirectResponse)
async def index_without_lang(request: Request):
    lang_header = request.headers["Accept-Language"]
    pref_lang = lang_header.split(',')[0].split(';')[0].strip().split('-')[0].lower() # get first language from header
    if pref_lang in app.locale.lang_list:
        if DEBUG:
            logger.debug(f"index_without_lang: in Accept-Language header: {lang_header} => pref_lang={pref_lang}")
        return RedirectResponse(url=f"/{pref_lang}/")
    return RedirectResponse(url=f"/{DEFAULT_LANG}/", status_code=308)

@app.get('/{lang}/', response_class=HTMLResponse)
async def index(request: Request, lang: str):
    request.session['lang'] = lang
    #check if user is already logged in in request.session, redirect to user if so
    user = request.session.get("user")
    if user:
        return RedirectResponse(url=f"/{lang}/user")
    
    return templates.TemplateResponse(name="index.jinja", context={"request": request,"hello": "world", "current_lang": lang, "lang_list": app.locale.lang_list, "page_title": app.locale.lang_str('home_page_title', lang)})

@app.get('/profile')
async def profile_without_lang(request: Request):
    lang_header = request.headers["Accept-Language"]
    pref_lang = lang_header.split(',')[0].split(';')[0].strip().split('-')[0].lower() # get first language from header
    if pref_lang in app.locale.lang_list:
        return RedirectResponse(url=f"/{pref_lang}/user")
    return RedirectResponse(url=f"/{DEFAULT_LANG}/user", status_code=308)
@app.get('/{lang}/profile')
async def profile(request: Request, lang: str):
    return RedirectResponse(url=f"/{lang}/user")
@app.get('/me')
async def me_without_lang(request: Request):
    lang_header = request.headers["Accept-Language"]
    pref_lang = lang_header.split(',')[0].split(';')[0].strip().split('-')[0].lower() # get first language from header
    if pref_lang in app.locale.lang_list:
        return RedirectResponse(url=f"/{pref_lang}/user")
    return RedirectResponse(url=f"/{DEFAULT_LANG}/user", status_code=308)
@app.get('/{lang}/me')
async def me(request: Request, lang: str):
    return RedirectResponse(url=f"/{lang}/user")


@app.get('/user', response_class=RedirectResponse)
async def user_without_lang(request: Request):
    lang_header = request.headers["Accept-Language"]
    pref_lang = lang_header.split(',')[0].split(';')[0].strip().split('-')[0].lower() # get first language from header
    if pref_lang in app.locale.lang_list:
        return RedirectResponse(url=f"/{pref_lang}/user")
    return RedirectResponse(url=f"/{DEFAULT_LANG}/user", status_code=308)

@app.get('/{lang}/user', response_class=HTMLResponse)
async def user(request: Request, lang: str, debug: Optional[str] = None, discorddebug: Optional[bool] = None):
    request.session['lang'] = lang
    if DEBUG:
        logger.debug(f"session.user: {request.session.get('user')}")
        if debug == APP_SECRET_KEY:
            logger.debug("Debug mode, user page accessed with app key")
            logger.debug(f"session: {request.session}")
            if discorddebug:
                return templates.TemplateResponse(name="user_with_discord.jinja", context={"request": request,"cas_username": "debug_username", "cas_email": "debug_email@example.org", "discord_id": "000", "discord_username": "@debug_discord_username", "current_lang": lang, "lang_list": app.locale.lang_list, "page_title": app.locale.lang_str('user_page_title', lang)})
            return templates.TemplateResponse(name="user.jinja", context={"request": request,"cas_username": "debug_username", "cas_email": "debug_email@example.org", "current_lang": lang, "lang_list": app.locale.lang_list, "page_title": app.locale.lang_str('user_page_title', lang)})
    user = request.session.get("user")
    if DEBUG:
        logger.debug(f"user: {user}")
    # ---------------- user was CAS authenticated ----------------
    if user:
        # %%%%%%%%%%%%% user is Discord authenticated %%%%%%%%%%%%%%%%%
        if await discord_auth.isAuthenticated(request.session['access_token']):
            return templates.TemplateResponse(name="user_with_discord.jinja", context={"request": request,"cas_username": user, "cas_email": "test","discord_id": request.session['discord_id'], "discord_username": request.session['discord_username'], "current_lang": lang, "lang_list": app.locale.lang_list, "page_title": app.locale.lang_str('user_page_title', lang)})
        # %%%%%%%%%%%%% user is not Discord authenticated %%%%%%%%%%%%%
        else:
            if DEBUG:
                cas_user = str(user['user'])
                logout_url = request.url_for('logout')
                return HTMLResponse(f'Logged in as {cas_user}. <a href="{logout_url}">Logout</a>')
            return templates.TemplateResponse(name="user.jinja", context={"request": request,"cas_username": user, "current_lang": lang, "lang_list": app.locale.lang_list, "page_title": app.locale.lang_str('user_page_title', lang)})
        # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # ---------------- user is not CAS authenticated ----------------
    elif request.session.get("discord_token"):
        if DEBUG:
            logger.debug("user: discord_token exists but user is not CAS authenticated")
    if DEBUG:
        login_url = request.url_for('login')
        return HTMLResponse(f'Login required. <a href="{login_url}">Login</a>', status_code=403)
    #return RedirectResponse(request.url_for('login'), status_code=403)
    return RedirectResponse(request.url_for('index'), status_code=403)
    # ---------------------------------------------------------------


@app.get('/login')
async def login(request: Request, next: Optional[str] = None, ticket: Optional[str] = None):
    service_ticket = ticket # ST from user to verify with CAS server
    if request.session.get("user", None):
        # Already logged in
        return RedirectResponse(request.url_for('user'))

    # next = request.args.get('next')
    # ticket = request.args.get('ticket')
    # ---------------- log in to CAS (redirect to CAS server) --------------------
    if not service_ticket: # first login -> redirect to CAS
        # No ticket, the request come from end user, send to CAS login
        cas_login_url = cas_client.get_login_url()
        if DEBUG:
            logger.debug(f'CAS login URL: {cas_login_url}')
        return RedirectResponse(cas_login_url)
    # ------ log in to this service (callback from CAS server with ticket) -------

    # There is a ticket, the request come from CAS as callback.
    # need call `verify_ticket()` to validate ticket and get user profile.
    if DEBUG:
        logger.debug(f'service_ticket: {service_ticket}')
        logger.debug(f'next: {next}')

    # Send service ticket (ST) to CAS server to verify, get back user details as xml/dict
    user_from_cas, attributes_from_cas, pgtiou = await cas_client.verify_ticket(service_ticket) # pgtIou means Proxy Granting Ticket IOU

    if DEBUG:
        logger.debug('CAS verify service_ticket response: user: %s, attributes: %s, pgtiou: %s', user_from_cas, attributes_from_cas, pgtiou)

    if not user_from_cas: # Failed to verify service_ticket
        login_url = request.url_for('login')
        if DEBUG:
            return HTMLResponse(f'Failed to verify ticket. <a href="{login_url}">Login</a>')
        return RedirectResponse(login_url)
    else:  # Login successfully, redirect according `next` query parameter.? or to /user
        #response = RedirectResponse(next)
        response = RedirectResponse(request.url_for('user'))
        request.session['user'] = dict(user=user_from_cas)
        return response


@app.get('/logout')
async def logout(request: Request):
    user = request.session.get("user")
    if user:
        redirect_url = request.url_for('logout_callback')
        cas_logout_url = cas_client.get_logout_url(redirect_url)
        if DEBUG:
            logger.debug('CAS logout URL: %s', cas_logout_url)
        return RedirectResponse(cas_logout_url)
    else:
        #login_url = request.url_for('login')
        #return HTMLResponse(f'Not logged in. <a href={login_url}>Login</a>')
        
        return RedirectResponse(request.url_for('login'))


@app.get('/logout-callback')
def logout_callback(request: Request):
    # redirect from CAS logout request after CAS logout successfully
    # response.delete_cookie('username')
    request.session.pop("user", None)
    
    #login_url = request.url_for('login')
    #return HTMLResponse(f'Logged out from CAS. <a href="{login_url}">Login</a>')
    
    return RedirectResponse(request.url_for('index'))


@app.get('/discord-login')
async def discord_login(request: Request):
    # check if already logged in with discord, redirect to user if so
    if request.session.get("discord_token"):
        return RedirectResponse(request.url_for('user'))

    #TODO:
    #user_session_state = generate_random(seed=request.session.items())
    #session_state = randomASCII(len=12)
    #session_state = hashlib.sha256(os.urandom(1024)).hexdigest()

    #logging.debug("discord_login: "+discord_auth.get_oauth_login_url(state="my_test_state"))
    return RedirectResponse(discord_auth.get_oauth_login_url(
        state="my_test_state" #TODO: generate state token ? based on user's session/request (like: used as seed)? see above commented
    )) # TODO: state https://discord.com/developers/docs/topics/oauth2#state-and-security
    #return await discord_auth.login(request) # ?
    #return await RedirectResponse(discord_auth.oauth_login_url) # or discord_auth.get_oauth_login_url(state="my state")


async def get_user(token: str = Depends(discord_auth.get_token)):
    if "identify" not in discord_auth.scopes:
        raise discord_auth.ScopeMissing("identify")
    route = "/users/@me"
    return DiscordUser(**(await discord_auth.request(route, token)))
    #return user

async def get_user_guilds(token: str = Depends(discord_auth.get_token)):
    if "guilds" not in discord_auth.scopes:
        raise discord_auth.ScopeMissing("guilds")
    route = "/users/@me/guilds"
    return [DiscordGuild(**guild) for guild in await discord_auth.request(route, token)]
    #return guilds

@app.get('/discord-callback')
async def discord_callback(request: Request, code: str, state: str):
    cas_user = request.session.get("user")
    if DEBUG or cas_user:
        token, refresh_token = await discord_auth.get_access_token(code) # ?
        #if getenv("DEBUG"):
        #    logging.debug(f"discord_callback: token={token}, refresh_token={refresh_token}")
        request.session['discord_refresh_token'] = refresh_token
        request.session['discord_token'] = token #await discord_auth.get_token(request=request) #! or just token from above ?

        user: DiscordUser = await get_user(token=token)
        if DEBUG:
            logger.debug(f"discord_callback: get_user: {user}")
        ##user: DiscordUser = await discord_auth.user(request=request)
        request.session['discord_username'] = user.username+(str(user.discriminator) if user.discriminator else "") # ?
        request.session["discord_global_name"] = user.global_name
        request.session["discord_id"] = user.id

        try:
            user_guilds: List[DiscordGuild] = await get_user_guilds(token=token)
            #if getenv("DEBUG"):
            #    logging.debug(f"discord_callback: user_guilds={user_guilds}")
            ##user_guilds: List[DiscordGuild] = await discord_auth.guilds()
            
            #request.session["discord_guilds"] = user_guilds
            #TODO: check which guilds that the user and the bot are both in, and only put the intersect in the session
        except:
            logger.error(f"ScopeMissing error in Discord API Client: missing \"guilds\" in scopes -> ignoring user guilds")

        assert state == "my_test_state" # compares state for security # TODO: state
        
        return RedirectResponse(request.url_for('user'))
        ##try:
        ##    await discord_auth.callback(request)
        ##    return RedirectResponse(request.url_for('user'))
        ##except Unauthorized:
        ##    return JSONResponse({"error": "Unauthorized"}, status_code=401)
        ##except RateLimited:
        ##    return JSONResponse({"error": "RateLimited"}, status_code=429)
        ##except ClientSessionNotInitialized:
        ##    return JSONResponse({"error": "ClientSessionNotInitialized"}, status_code=500)
    else:
        return RedirectResponse(request.url_for('login'))


#! needed ?
@app.get(
    "/authenticated",
    response_model=bool,
)
async def isAuthenticated(request: Request):
    try:
        auth = await discord_auth.isAuthenticated(token=request.session['discord_token'])
        return auth
    except Unauthorized:
        return False


@app.get('/discord-logout')#, dependencies=[Depends(discord_auth.requires_authorization)])
async def discord_logout(request: Request):#, token: str = Depends(discord_auth.get_token)):
    try:
        #if await discord_auth.isAuthenticated(token):
        if await discord_auth.isAuthenticated(request.session['discord_token']):
            if DEBUG:
                logger.debug("discord_logout: isAuthenticated=True")
    #if await discord_auth.isAuthenticated(request.session['access_token']):
            
            # TODO: sufficient ?

            #await discord_auth.revoke(request.session['discord_token']) #? not in fastapi-discord ?
            # see https://github.com/treeben77/discord-oauth2.py/blob/main/discordoauth2/__init__.py#L242
            if DEBUG:
                logger.debug("discord_logout: revoking discord_token")
            await revoke_discord_token(request.session['discord_token'], "access_token", request.session['discord_username'])
            if DEBUG:
                logger.debug("discord_logout: revoking discord_refresh_token")
            await revoke_discord_token(request.session['discord_refresh_token'], "refresh_token", request.session['discord_username'])

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
    except KeyError:
        if request.session['lang'] in app.locale.lang_list:
            return RedirectResponse(url=f"/{request.session['lang']}/user")
        else:
            return RedirectResponse(url=f"/{DEFAULT_LANG}/user")

# FIXME: #! doesn't seem to be working ?
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
        
    if response.status_code == 200:# or response.status_code.OK ?:
        if DEBUG:
            logger.debug(f"revoke_discord_token: Discord token (type:{token_type}) revoked successfully for user:{user}.")
        return True
    elif response.status_code == 401:
        logger.error(f"revoke_discord_token: 401 This AccessToken does not have the necessary scope.")
    elif response.status_code == 429:
        logger.error(f"revoke_discord_token: 429 You are being Rate Limited. Retry after: {response.json()['retry_after']}")
    else:
        logger.error(f"revoke_discord_token: Unexpected HTTP response {response.status_code}")
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

    botLogFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    botRootLogger = logging.getLogger()
    botRootLogger.setLevel(logging.DEBUG) # if DEBUG else logging.TRACE ?

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(botLogFormatter)
    consoleHandler.setLevel(logging.TRACE)
    botRootLogger.addHandler(consoleHandler)

    if platform.system() == "Linux":
        fileInfoHandler = logging.handlers.RotatingFileHandler(
            filename="logs/info.log", mode="w", encoding="UTF-8", delay=True, backupCount=5
        )
        fileDebugHandler = logging.handlers.RotatingFileHandler(
            filename="logs/debug.log", mode="w", encoding="UTF-8", delay=True, backupCount=5
        )
        fileInfoHandler.setFormatter(botLogFormatter)
        fileInfoHandler.setLevel(logging.TRACE)
        fileInfoHandler.doRollover()
        botRootLogger.addHandler(fileInfoHandler)
        fileDebugHandler.setFormatter(botLogFormatter)
        fileDebugHandler.setLevel(logging.DEBUG)
        fileDebugHandler.doRollover()
        botRootLogger.addHandler(fileDebugHandler)

    else:
        logging.warning("Non-Linux system. INFO and DEBUG log files won't be available.")

    bot = Bot(logger=botRootLogger, logFormatter=botLogFormatter)
    #await bot.run(getenv("DISCORD_BOT_TOKEN")) # TODO: implement bot

# ? needed ?
async def run_web():
    try:
        logger.info("Run webapp")
        #await uvicorn.run(app, port=getenv('FASTAPI_PORT', 8000), host=getenv('FASTAPI_HOST', 'localhost')) # ?
    except:
        logger.error("Webapp fail")
    
if __name__ == '__main__':
    import uvicorn

    init()

    #TODO: start Discord bot
    
    #if not getenv("BOT_DISABLED"):
    #    asyncio.create_task(run_bot()) # ? run Discord bot async


    if DEBUG:
        logger.debug("Running FastAPI webapp with reload")
        uvicorn.run("app:app", port=int(getenv('FASTAPI_PORT', 8000)), host=str(getenv('FASTAPI_HOST', 'localhost')), reload=True)
    else:
        logger.info("Running FastAPI webapp")
        uvicorn.run("app:app", port=int(getenv('FASTAPI_PORT', 8000)), host=str(getenv('FASTAPI_HOST', 'localhost')))
    #asyncio.create_task(run_web()) # ? run FastAPI webapp async

