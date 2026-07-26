from fastapi import APIRouter
from typing import Optional
import database as db
from models.schemas import SchemeCreate

router = APIRouter(prefix="/api/schemes", tags=["Schemes"])

@router.get("")
async def get_schemes(query: Optional[str] = None, category: Optional[str] = None):
    results = await db.search_schemes(query=query, category=category)
    return results

@router.post("", status_code=201)
async def create_scheme(scheme: SchemeCreate):
    result = await db.add_scheme(scheme.dict())
    return {"status": "success", "scheme": result}
