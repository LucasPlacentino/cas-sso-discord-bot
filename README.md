<img padding-left="5px" align="right" height="300" src="https://github.com/LucasPlacentino/cas-sso-discord-bot/assets/23436953/647500ce-aef6-4cb3-bfba-5a8ef0bb4a8e.png">

# cas-sso-discord-bot
A Discord bot and FastAPI webapp for authenticating users using CAS SSO.  
Links their Discord account (ID) to their CAS credentials. Users are able to link and unlink their account, and only one Discord ID can be linked to a CAS user.  

FastAPI, Disnake, CAS, [some database TBD], Docker, Discord OAuth2, etc.

### Currently at the dev stage
Possibly replacing [our own previous auth bot **ULBDiscordBot**](https://github.com/bepolytech/ULBDiscordBot) which was just based on email-sent tokens.  

Uses:
- [FastAPI](https://github.com/tiangolo/fastapi)
- [Disnake](https://github.com/DisnakeDev/disnake)
- [fastapi_discord](https://github.com/Tert0/fastapi-discord)
- [python-cas](https://github.com/python-cas/python-cas)

> [Opensource-IIITH/Discord-CAS](https://github.com/Opensource-IIITH/Discord-CAS)
> 
> OR use:  
> 
> - https://discord.com/developers/docs/tutorials/configuring-app-metadata-for-linked-roles  
> - https://github.com/discord/linked-roles-sample  
> - https://support.discord.com/hc/en-us/articles/10388356626711-Connections-Linked-Roles-Admins  
>   
> - https://apereo.github.io/2019/02/19/cas61-as-oauth-authz-server/  
> 
> - https://github.com/weibeu/Flask-Discord => fastapi instead (but missing stuff like revoke() etc)  
> or  
> - https://github.com/treeben77/discord-oauth2.py  

## Acknowledgments
- [**ULBDiscordBot**](https://github.com/bepolytech/ULBDiscordBot): predecessor to this bot
- [**DocHub**](https://github.com/DocHub-ULB/DocHub): student-made ULB courses documents and summaries repository accessible via ULB's CAS auth.  
