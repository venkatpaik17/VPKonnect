from fastapi import APIRouter

from app.api.v0.routes import auth, user

router = APIRouter()

router.include_router(user.router)
router.include_router(auth.router)
