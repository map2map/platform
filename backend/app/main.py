from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.auth import router as auth_router
import os

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://platform-frontend-acoh.onrender.com",
        "https://map2map.com",  # Production
        "http://localhost:5173"  # For local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])

@app.get("/")
async def root():
    return {"message": "Map2Map API is running"}

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")

@app.post("/auth/callback")
async def auth_callback(payload: dict):
    # Validate Google credential and retrieve user info
    user = await verify_google_credential(payload.get("credential"))
    # Create JWT for your application
    jwt = create_jwt_for_user(user)

    return {"token": jwt, "user": {"name": user.name, "email": user.email}}
