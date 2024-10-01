> implement a simpler way to auth via ulb CAS, using FastAPI (from DocHub)

### Current Implementation Overview
The `users/views.py` file handles ULB CAS authentication using Django. The key points are:
- **login_view**: Redirects to the CAS login URL and sets a `next_url` cookie if provided.
- **auth_ulb**: Retrieves the CAS ticket, authenticates the user, handles various exceptions, logs in the user, and redirects based on the `next_url` cookie.

### Implementing CAS Authentication with FastAPI
Here’s a basic outline for implementing CAS authentication using FastAPI:

1. **Install FastAPI and Dependencies**
   ```bash
   pip install fastapi uvicorn requests
   ```

2. **Create a FastAPI Application**
   ```python
   from fastapi import FastAPI, Request, HTTPException, Depends
   from fastapi.responses import RedirectResponse
   from fastapi.security import OAuth2PasswordBearer
   import requests

   app = FastAPI()
   oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

   CAS_SERVER = "https://cas.example.com"
   SERVICE_URL = "http://localhost:8000/auth/callback"

   def get_login_url():
       return f"{CAS_SERVER}/login?service={SERVICE_URL}"

   def validate_ticket(ticket: str):
       validate_url = f"{CAS_SERVER}/validate?service={SERVICE_URL}&ticket={ticket}"
       response = requests.get(validate_url)
       if response.status_code == 200:
           _, user = response.text.split("\n")
           return user
       return None

   @app.get("/auth/login")
   async def login(next: str = None):
       response = RedirectResponse(url=get_login_url())
       if next:
           response.set_cookie("next_url", next, max_age=600)
       return response

   @app.get("/auth/callback")
   async def callback(request: Request, ticket: str):
       user = validate_ticket(ticket)
       if not user:
           raise HTTPException(status_code=400, detail="Invalid ticket")
       
       # Simulate login
       request.state.user = user
       
       next_url = request.cookies.get("next_url")
       response = RedirectResponse(url=next_url or "/")
       response.delete_cookie("next_url")
       return response

   @app.get("/protected")
   async def protected(user: str = Depends(oauth2_scheme)):
       return {"message": f"Hello, {user}"}
   ```

3. **Run the FastAPI Application**
   ```bash
   uvicorn yourfilename:app --reload
   ```

### Next Steps
1. Integrate this basic example into your existing FastAPI project.
2. Adapt the user retrieval and session management to fit your specific needs.

Feel free to ask if you need further adjustments or details!