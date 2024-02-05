# cas-sso-discord-bot

from typing import Optional, List

from cas import CASClient # https://github.com/Chise1/fastapi-cas-example
from fastapi import FastAPI, Depends, Request
from starlette.middleware.sessions import SessionMiddleware
#from starlette.requests import Request
#from starlette.responses import Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_discord import DiscordOAuthClient, RateLimited, Unauthorized, User # https://github.com/Tert0/fastapi-discord
from fastapi_discord.exceptions import ClientSessionNotInitialized
from fastapi_discord.models import GuildPreview
#* OR ? :
#* from starlette_discord.client import DiscordOAuthClient # https://github.com/nwunderly/starlette-discord
from os import getenv

app = FastAPI(title=__name__)
app.mount("/static", StaticFiles(directory="static"), name="static")
from fastapi.responses import RedirectResponse

cas_client = CASClient(
    version=getenv('CAS_VERSION'),
    service_url=getenv('CAS_SERVICE_URL'),
    server_url=getenv('CAS_SERVER_URL'),
)
app.add_middleware(SessionMiddleware, secret_key=getenv('SECRET'))

discord_auth = DiscordOAuthClient(
    client_id=getenv('DISCORD_CLIENT_ID'),
    client_secret=getenv('DISCORD_CLIENT_SECRET'),
    #redirect_url=getenv('DISCORD_REDIRECT_URL'),
    redirect_url=str(getenv("SITE_URL", "http://localhost:8000"))+"/discord-callback",
    scopes=("identify")#, "guilds", "email") # scopes
)
DISCORD_TOKEN_URL = "https://discord.com/api/v10/oauth2/token" # ? https://github.com/Tert0/fastapi-discord/issues/96

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def on_startup():
    await discord_auth.init()


@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"hello": "world"}
    )


@app.get('/user', response_class=HTMLResponse)
async def profile(request: Request):
    print(request.session.get("user"))
    user = request.session.get("user")
    if user:
        if await discord_auth.isAuthenticated(request.session['access_token']):
            return templates.TemplateResponse(request=request, name="user_with_discord.html", context={"cas_username": user, "discord_id": discord_auth.id, "discord_username": discord_auth.username})
        else:
            return HTMLResponse('Logged in as %s. <a href="/logout">Logout</a>' % user['user'])
    return HTMLResponse('Login required. <a href="/login">Login</a>', status_code=403)


@app.get('/login')
def login(
    request: Request, next: Optional[str] = None,
    ticket: Optional[str] = None):
    if request.session.get("user", None):
        # Already logged in
        return RedirectResponse(request.url_for('profile'))

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

    user, attributes, pgtiou = cas_client.verify_ticket(ticket)

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
def logout(request: Request):
    redirect_url = request.url_for('logout-callback')
    cas_logout_url = cas_client.get_logout_url(redirect_url)
    print('CAS logout URL: %s', cas_logout_url)
    return RedirectResponse(cas_logout_url)


@app.get('/logout-callback')
def logout_callback(request: Request):
    # redirect from CAS logout request after CAS logout successfully
    # response.delete_cookie('username')
    request.session.pop("user", None)
    return HTMLResponse('Logged out from CAS. <a href="/login">Login</a>')


@app.get('/discord-login')
async def discord_login(request: Request):
    return await RedirectResponse(discord_auth.get_oauth_login_url(state="my_test_state")) # TODO: state https://discord.com/developers/docs/topics/oauth2#state-and-security
    return await discord_auth.login(request) # ?
    #return await RedirectResponse(discord_auth.oauth_login_url) # or discord_auth.get_oauth_login_url(state="my state")


@app.get('/discord-callback')
async def discord_callback(request: Request, code: str, state: str):
    token, refresh_token = await discord_auth.get_access_token(code)
    request.session['discord_token'] = await discord_auth.get_token

    assert state == "my_test_state" # compares state for security # TODO: state
    
    return await RedirectResponse(request.url_for('user'))
    #try:
    #    await discord_auth.callback(request)
    #    return RedirectResponse(request.url_for('user'))
    #except Unauthorized:
    #    return JSONResponse({"error": "Unauthorized"}, status_code=401)
    #except RateLimited:
    #    return JSONResponse({"error": "RateLimited"}, status_code=429)
    #except ClientSessionNotInitialized:
    #    return JSONResponse({"error": "ClientSessionNotInitialized"}, status_code=500)


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


@app.get('/discord-logout')
async def discord_logout(request: Request):
    pass


@app.exception_handler(Unauthorized)
async def unauthorized_error_handler(request: Request):
    error = "Unauthorized"
    return HTMLResponse(templates.TemplateResponse(request=request, name="401.html", context={"error": error}), status_code=401)
    return JSONResponse({"error": "Unauthorized"}, status_code=401)


@app.exception_handler(RateLimited)
async def rate_limit_error_handler(request: Request, e: RateLimited):
    return HTMLResponse(templates.TemplateResponse(request=request, name="429.html", context={"retry_after": e.retry_after}), status_code=429)
    return JSONResponse(
        {"error": "RateLimited", "retry": e.retry_after, "message": e.message},
        status_code=429,
    )


@app.exception_handler(ClientSessionNotInitialized)
async def client_session_error_handler(request: Request, e: ClientSessionNotInitialized):
    print(e)
    return HTMLResponse(templates.TemplateResponse(request=request, name="500.html", context={"error": e}), status_code=500)
    return JSONResponse({"error": "Internal Error"}, status_code=500)


if __name__ == '__main__':
    import uvicorn

    #TODO: start Discord bot

    uvicorn.run(app, port=getenv('PORT', 8000), host=getenv('HOST', '0.0.0.0'))

