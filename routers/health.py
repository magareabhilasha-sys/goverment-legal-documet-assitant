from fastapi import APIRouter
import database as db
import services.gemini_service as gemini

router = APIRouter(prefix="/api/health", tags=["Health"])

@router.get("")
async def health_check():
    return {
        "status": "healthy",
        "database_mode": "mock_in_memory" if db.MOCK_MODE else "mongodb",
        "gemini_connected": gemini.has_gemini
    }
