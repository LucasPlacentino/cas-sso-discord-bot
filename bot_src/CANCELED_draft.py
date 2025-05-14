import aiohttp
from aiohttp import web
import disnake
import time
from collections import defaultdict
from disnake.ext import commands
from dotenv import load_dotenv
from os import getenv
load_dotenv()

# --- test: ---
from aiolimiter import AsyncLimiter # need to pip install aiolimiter

# Strict for unauthenticated IPs
strict_limiters = defaultdict(lambda: AsyncLimiter(10, 1))   # 10 r/s/IP
# Lax for trusted IPs
trusted_limiters = defaultdict(lambda: AsyncLimiter(1000, 1)) # 1000 r/s/IP
# Track which IPs have authed successfully at least once
trusted_ips = set()

BEHIND_PROXY = getenv("BEHIND_PROXY", False)  # Set to True if behind a reverse proxy (e.g., Nginx)

@web.middleware
async def rate_limit_middleware(request, handler):
    if BEHIND_PROXY:
        client_ip = request.headers.get("X-Forwarded-For", request.remote) # or request.headers.get("X-Real-IP") ?
    else:
        client_ip = request.remote

    # Choose limiter based on IP trust
    if client_ip in trusted_ips:
        limiter = trusted_limiters[client_ip]
    else:
        limiter = strict_limiters[client_ip]

    # Apply the appropriate rate limiter
    if not limiter.has_capacity():
        # If the rate limit is exceeded, return a 429 response
        return json_error_response(
            error_code="rate_limited",
            message="Rate limit exceeded, please try again later",
            http_status=web.HTTPTooManyRequests.status # 429
        )
        # return web.json_response({
        #     "success": False,
        #     "error": {
        #         "code": "rate_limited",
        #         "message": "Too many requests"
        #     }
        # }, status=429)

    async with limiter:
        # Proceed with the request, check api key for authentication
        api_key = request.headers.get("X-API-Key")
        # If authed correctly, promote IP to trusted
        if api_key == API_SECRET_KEY:
            trusted_ips.add(client_ip)
            return await handler(request) # Proceed with the request
        else:
            # If not authed, return unauthorized response
            # raise web.HTTPUnauthorized(
            #     reason="Invalid or missing API key",
            #     headers={"X-Error": "Invalid or missing API key"}
            # )
            return json_error_response(
                error_code="unauthorized",
                message="Invalid or missing API key",
                http_status=web.HTTPUnauthorized.status # 401
            )
            # return web.json_response({
            #     "success": False,
            #     "error": {
            #         "code": "unauthorized",
            #         "message": "Invalid or missing API key"
            #     }
            # }, status=401)
# ------

# Initialize the Disnake bot
intents = disnake.Intents.default()
bot = disnake.Client(intents=intents)
BOT_TOKEN = "your-bot-token"  # Replace with your bot token

# Authentication Middleware (Secret Key)
API_SECRET_KEY = "your-secret-api-key"  # This secret should be shared with the webapp

#! OR USE https://github.com/mjpieters/aiolimiter ?
# Rate Limiting Middleware (Simple in-memory rate limit)
rate_limits = defaultdict(list)  # To track request timestamps for each IP

# Time window for rate-limiting (e.g., 1 minute)
RATE_LIMIT_WINDOW = 60  # seconds
MAX_REQUESTS_PER_WINDOW = 5  # Max requests allowed in the rate limit window

# Disnake bot command prefix
bot_prefix = "!"
bot = commands.Bot(command_prefix=bot_prefix)

# utils:
def json_success_response(message: str, data: dict = None) -> web.Response:
    return web.json_response(
        {
            "success": True,
            "message": message,
            "data": data
        }
    )
def json_error_response(error_code: str, message: str, http_status: int = 400) -> web.Response:
    return web.json_response(
        {
            "success": False,
            "error": {
                "code": error_code,
                "message": message
            }
        },
        status=http_status
    )


# ? https://us-pycon-2019-tutorial.readthedocs.io/aiohttp_server.html ?

# --- Custom middleware for authentication (and rate-limiting) : ---
async def auth_middleware(app, handler):
    async def middleware_handler(request):
        # Authentication: Check the secret key in the headers
        api_key = request.headers.get('X-API-KEY')
        if api_key != API_SECRET_KEY:
            return json_error_response(error_code="unauthorized", message="Unauthorized access", http_status=401)
            #return web.json_response({"error": "Unauthorized"}, status=401)
        

        #! better to use https://github.com/mjpieters/aiolimiter ?

        # # Rate-limiting: Check the number of requests from the IP in the time window
        # #client_ip = request.remote
        # client_ip = request.headers.get("X-Forwarded-For", request.remote) # because behind a reverse proxy (nginx)
        # current_time = time.time()
        
        # # Clean up expired timestamps
        # rate_limits[client_ip] = [timestamp for timestamp in rate_limits[client_ip] if current_time - timestamp < RATE_LIMIT_WINDOW]
        
        # # Check if the number of requests is within the limit
        # if len(rate_limits[client_ip]) >= MAX_REQUESTS_PER_WINDOW:
        #     return json_error_response(error_code="rate_limit_exceeded", message="Rate limit exceeded, please try again later", http_status=429)
        #     #return web.json_response({"error": "Rate limit exceeded, please try again later"}, status=429)
        
        # # Allow request and record the timestamp
        # rate_limits[client_ip].append(current_time)
        
        return await handler(request)

    return middleware_handler
# ------

# Add authentication and rate-limiting middleware
#app = web.Application(middlewares=[auth_middleware])
# ? test:
app = web.Application(middlewares=[rate_limit_middleware, auth_middleware]) # Add rate limit middleware

routes = web.RouteTableDef()

# Define the task endpoints
@routes.post("/add-role")
async def handle_add_role(request):
    """
    example_data = {
        "user_id": 000,
        "role_id": 000
    }
    """
    data = await request.json()
    user_id = data.get('user_id')
    role_id = data.get('role_id') # no the role id wont be sent with the request, it will be in the bot's memory/database
    
    user = await bot.get_user_info(user_id)
    role = disnake.utils.get(user.guild.roles, id=role_id) # not correct ?
    if role:
        await user.add_roles(role)
        return json_success_response(message=f"Role {role.name} (id={role_id}) added to {user.name} (id={user_id})", data=data)
        #return web.json_response({"success": True,"message": f"Role {role.name} (id={role_id}) added to {user.name} (id={user_id})", "data": data})
    else:
        #return json_error_response(error_code="role_not_found", message=f"Role with id {role_id} not found", http_status=404)
        return json_error_response(error_code="role_not_found", message=f"Role with id {role_id} not found", http_status=web.HTTPNotFound.status) # 404
        #return web.json_response({"success": False, "error": {"code": "role_not_found", "message": f"Role with id {role_id} not found"}}, status=404)

@routes.post("/send-message")
async def handle_send_message(request):
    """
    example_data = {
        "user_id": 000,
        "message": "Example"
    }
    """
    data = await request.json()
    user_id = data.get('user_id')
    message = data.get('message')
    
    user = await bot.get_user_info(user_id)
    await user.send(message)
    return json_success_response(message=f"Message sent to {user.name}: {message}", data=data)
    #return web.json_response({"success": True, "message": f"Message sent to {user.name}: {message}", "data": data})

# # Add routes for the bot actions
# app.router.add_post("/add-role", handle_add_role)
# app.router.add_post("/send-message", handle_send_message)

# Register the routes with the aiohttp web app
app.add_routes(routes)

# Run the aiohttp web app and the bot in parallel
async def start_bot():
    await bot.start(BOT_TOKEN)

# Run the bot with Uvicorn and aiohttp web server
if __name__ == "__main__":
    import uvicorn
    import asyncio

    # Run the aiohttp server and bot concurrently
    asyncio.run(asyncio.gather(
        start_bot(),
        uvicorn.run(app, host="0.0.0.0", port=8001)
    ))

    # # OR :
    # runner = web.AppRunner(app)
    # await runner.setup()
    # site = web.TCPSite(runner, 'localhost', 8080)
    # await site.start()
