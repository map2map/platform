from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import RedirectResponse, JSONResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
import json
from datetime import datetime, timedelta
import jwt as pyjwt
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

# This would typically be in your main FastAPI app setup
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://platform-frontend-acoh.onrender.com",
        "http://localhost:5173"  # For local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

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
        "redirect_uris": ["https://platform-krns.onrender.com/auth/callback"],  # Backend URL
        "javascript_origins": ["https://platform-frontend-acoh.onrender.com"]  # Frontend URL
    }
}

# Update scopes to include openid
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

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
        # Create a new flow for each login attempt
        flow = Flow.from_client_config(
            CLIENT_CONFIG,
            scopes=SCOPES,
            redirect_uri=CLIENT_CONFIG["web"]["redirect_uris"][0],
            state=os.urandom(16).hex()  # Generate a random state
        )
        
        # Generate the authorization URL with additional parameters
        # Note: authorization_url() returns a tuple of (url, state)
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='select_account',  # Force account selection
            hd='*'  # Allow any Google domain
        )
        
        # Store the state in the session or database if needed
        # For now, we'll just log it for debugging
        print(f"Generated OAuth state: {state}")
        
        # Return a proper redirect response
        return RedirectResponse(url=authorization_url)
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to initialize OAuth flow: {str(e)}"
        )

# In-memory store for OAuth states (use a proper cache in production)
oauth_states = {}

@router.get("/callback")
async def callback(request: Request):
    try:
        # Get the authorization code and state from the request
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        error = request.query_params.get("error")
        
        if error:
            raise HTTPException(
                status_code=400,
                detail=f"OAuth error: {error}. Description: {request.query_params.get('error_description', 'No description')}"
            )
            
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code not found")
        
        # Verify state parameter to prevent CSRF
        if not state:
            raise HTTPException(status_code=400, detail="State parameter missing")
            
        # In a production app, you would validate the state against your session
        # For now, we'll just log it
        print(f"Received OAuth state: {state}")
        
        # Initialize a new flow for each request
        flow = Flow.from_client_config(
            CLIENT_CONFIG,
            scopes=SCOPES,
            redirect_uri=CLIENT_CONFIG["web"]["redirect_uris"][0],
            state=state  # Pass the state back for validation
        )
        
        # Exchange the code for credentials
        try:
            flow.fetch_token(
                code=code,
                # Add these parameters to prevent token reuse issues
                client_secret=CLIENT_CONFIG["web"]["client_secret"],
                include_granted_scopes='true'
            )
        except Exception as e:
            print(f"Token exchange failed: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to exchange authorization code: {str(e)}"
            )
            
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
        
        # Build the frontend URL with token
        frontend_url = "https://platform-frontend-acoh.onrender.com/auth/callback"
        redirect_url = f"{frontend_url}#token={access_token}"
        
        # Create response with CORS headers
        response = JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "access_token": access_token,
                "token_type": "bearer",
                "redirect": "/"
            }
        )
        
        # Set the HTTP-only cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,  # Set to True for HTTPS
            samesite="lax",
            max_age=86400,  # 1 day
            domain="platform-frontend-acoh.onrender.com"  # Set to exact domain
        )
        
        # Add CORS headers
        response.headers["Access-Control-Allow-Origin"] = "https://platform-frontend-acoh.onrender.com"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        # For development, also allow localhost
        response.headers["Access-Control-Allow-Origin"] = os.getenv(
            "FRONTEND_URL", 
            "https://platform-frontend-acoh.onrender.com,http://localhost:5173"
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
    response = RedirectResponse(url="https://platform-frontend-acoh.onrender.com")
    response.delete_cookie("access_token")
    return response
