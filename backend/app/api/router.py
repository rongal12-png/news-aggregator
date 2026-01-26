from fastapi import APIRouter

from .endpoints import health, sources, stories, admin, auth, comments

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
api_router.include_router(stories.router, prefix="/stories", tags=["stories"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(comments.router, prefix="/comments", tags=["comments"])
