from fastapi import APIRouter

from app.api.v0.routes import admin, auth, comment, employee, post, user

router = APIRouter()

router.include_router(user.router)
router.include_router(auth.router)
router.include_router(admin.router)
router.include_router(employee.router)
router.include_router(post.router)
router.include_router(comment.router)
