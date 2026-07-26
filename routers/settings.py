from fastapi import APIRouter
import services.gemini_service as gemini
from models.schemas import ApiKeyUpdate

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.post("/apikey")
async def change_api_key(payload: ApiKeyUpdate):
    gemini.update_api_key(payload.api_key)
    return {"status": "success", "gemini_connected": gemini.has_gemini}
