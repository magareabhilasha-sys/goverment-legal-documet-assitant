from fastapi import APIRouter
import database as db

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("")
async def get_analytics_dashboard():
    stats = await db.get_analytics()
    return stats
