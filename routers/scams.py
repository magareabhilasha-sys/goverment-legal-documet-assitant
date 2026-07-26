from fastapi import APIRouter
import database as db
import services.gemini_service as gemini
from models.schemas import ScamCheckRequest, ScamCheckResponse

router = APIRouter(prefix="/api/scams", tags=["Scams"])

@router.post("/check", response_model=ScamCheckResponse)
async def check_scam(request: ScamCheckRequest):
    result = await gemini.detect_scam(request.text)
    await db.save_scam_log(request.text, result)
    return ScamCheckResponse(**result)
