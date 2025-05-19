from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/")
async def root():
    return {"message": "Auth router is working"}
