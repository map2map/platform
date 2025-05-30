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
from pydantic import BaseModel

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
        "client_id": "204371247654-3i8cj8r08biinvd322mjh3fs6s8dnee1.apps.googleusercontent.com",
        "project_id": "map2map",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uris": ["https://platform-krns.onrender.com/auth/callback"],
        "javascript_origins": ["https://platform-frontend-acoh.onrender.com"]
    }
}

# Secret key for JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"

class GoogleCredential(BaseModel):
    credential: str

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=1)
    to_encode.update({"exp": expire})
    encoded_jwt = pyjwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/callback")
async def callback(credential_data: GoogleCredential):
    try:
        # Decode the Google ID token
        credential = credential_data.credential
        decoded_token = pyjwt.decode(credential, options={"verify_signature": False})
        
        # Create JWT token
        token_data = {
            "sub": decoded_token["sub"],
            "email": decoded_token["email"],
            "name": decoded_token.get("name", ""),
            "picture": decoded_token.get("picture", "")
        }
        access_token = create_access_token(token_data)
        
        # Return token and user info in response body
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "token": access_token,
                "user": {
                    "id": token_data["sub"],
                    "email": token_data["email"],
                    "name": token_data["name"],
                    "picture": token_data["picture"]
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@router.get("/check")
async def check_auth(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.split(" ")[1]
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
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Logged out successfully"}
    )
