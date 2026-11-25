from fastapi import APIRouter, Depends
from app.api.v1.endpoints import (
    auth,
    exports,
    intake,
    projects,
    research,
    settings,
    storage,
    studio,
    vault,
)
from app.core.security import verify_studio_session
from app.schemas.common import ok_response

api_v1_router = APIRouter(prefix="/api/v1")


@api_v1_router.get("/health")
async def health_check():
    return ok_response({"status": "healthy", "service": "geotechnical-survey-ai-api"})


api_v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_v1_router.include_router(storage.router, prefix="/storage", tags=["storage"])

protected_deps = [Depends(verify_studio_session)]
api_v1_router.include_router(
    settings.router, prefix="/settings", tags=["settings"], dependencies=protected_deps
)
api_v1_router.include_router(
    vault.router, prefix="/vault", tags=["vault"], dependencies=protected_deps
)
api_v1_router.include_router(
    projects.router, prefix="/projects", tags=["projects"], dependencies=protected_deps
)
api_v1_router.include_router(
    intake.router, prefix="/projects", tags=["intake"], dependencies=protected_deps
)
api_v1_router.include_router(
    studio.router, prefix="/projects", tags=["studio"], dependencies=protected_deps
)
api_v1_router.include_router(
    exports.router, prefix="/projects", tags=["exports"], dependencies=protected_deps
)
api_v1_router.include_router(
    research.router, prefix="/research", tags=["research"], dependencies=protected_deps
)
