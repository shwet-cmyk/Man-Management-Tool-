from fastapi import APIRouter

from app.product_intelligence.api.ai_recommendation_router import router as ai_router
from app.product_intelligence.api.heatmap_router import router as heatmap_router
from app.product_intelligence.api.help_refresh_router import router as help_router
from app.product_intelligence.api.release_notes_router import router as release_router
from app.product_intelligence.api.telemetry_router import router as telemetry_router

router = APIRouter(tags=['Product Intelligence'])
router.include_router(telemetry_router)
router.include_router(heatmap_router)
router.include_router(ai_router)
router.include_router(release_router)
router.include_router(help_router)
