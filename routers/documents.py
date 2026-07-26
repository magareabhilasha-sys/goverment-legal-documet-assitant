import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import services.rag_service as rag

logger = logging.getLogger("documents_router")
router = APIRouter(prefix="/api/documents", tags=["Documents"])

@router.post("/upload")
async def upload_document(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF documents are supported.")
        
    try:
        content = await file.read()
        result = await rag.add_document(session_id, content, file.filename)
        if not result.get("success", False):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to parse PDF"))
        return result
    except Exception as e:
        logger.error(f"Error handling file upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))
