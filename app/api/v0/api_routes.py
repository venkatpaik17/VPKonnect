from fastapi import APIRouter

from app.api.v0.routes import user

router = APIRouter()

router.include_router(user.router)
