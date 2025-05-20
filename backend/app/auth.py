from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
import json
from datetime import datetime, timedelta
import jwt as pyjwt

router = APIRouter()

# Load OAuth 2.0 credentials from environment variables
CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "project_id": "map2map",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")],
        "javascript_origins": [os.getenv("FRONTEND_URL", "http://localhost:5173")]
    }
}

SCOPES = ['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']

# Secret key for JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=1)
    to_encode.update({"exp": expire})
    encoded_jwt = pyjwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.get("/login")
async def login():
    try:
        flow = Flow.from_client_config(
            CLIENT_CONFIG,
            scopes=SCOPES,
            redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")
        )
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        return RedirectResponse(authorization_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize OAuth flow: {str(e)}")

@router.get("/callback")
async def callback(request: Request):
    try:
        flow = Flow.from_client_config(
            CLIENT_CONFIG,
            scopes=SCOPES,
            redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")
        )
        
        # Get the authorization code from the request
        code = request.query_params.get("code")
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code not found")
        
        # Exchange the code for credentials
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Get user info from Google
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        
        # Create JWT token
        token_data = {
            "sub": user_info["id"],
            "email": user_info["email"],
            "name": user_info.get("name", ""),
            "picture": user_info.get("picture", "")
        }
        access_token = create_access_token(token_data)
        
        # Redirect to frontend with token
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        response = RedirectResponse(url=f"{frontend_url}/auth/callback")
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=86400  # 1 day
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@router.get("/check")
async def check_auth(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "user": {
                "id": payload["sub"],
                "email": payload["email"],
                "name": payload["name"],
                "picture": payload.get("picture", "")
            }
        }
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except pyjwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/logout")
async def logout():
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    response = RedirectResponse(url=frontend_url)
    response.delete_cookie("access_token")
    return response
