"""
Central API router combining all v1 route modules.
"""
from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.vets import router as vets_router
from app.api.v1.accidents import router as accidents_router
from app.api.v1.reports import router as reports_router
from app.api.v1.pets import router as pets_router
from app.api.v1.donations import router as donations_router
from app.api.v1.admin import router as admin_router
from app.api.v1.media import router as media_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(vets_router)
api_v1_router.include_router(accidents_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(pets_router)
api_v1_router.include_router(donations_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(media_router)


