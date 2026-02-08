import os
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List

from config import KNOWLEDGE_BASE_DIR
from models.schemas import KnowledgeFile
from services.rag_service import get_rag_service

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md"}


@router.get("/files", response_model=List[KnowledgeFile])
async def list_files():
    """List all files in the knowledge base."""
    rag = get_rag_service()
    files = rag.list_files()

    return [
        KnowledgeFile(
            id=f["id"],
            filename=f["filename"],
            file_type=f["file_type"],
            file_size=f["file_size"],
            chunk_count=f["chunk_count"],
            uploaded_at=datetime.fromisoformat(f.get("uploaded_at", datetime.now().isoformat()))
        )
        for f in files
    ]


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a new document to the knowledge base."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {ext} not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Save file
    safe_filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = KNOWLEDGE_BASE_DIR / safe_filename

    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Add to RAG
        rag = get_rag_service()
        file_info = rag.add_document(str(file_path), safe_filename)

        return {
            "success": True,
            "file": KnowledgeFile(
                id=file_info["id"],
                filename=file_info["filename"],
                file_type=file_info["file_type"],
                file_size=file_info["file_size"],
                chunk_count=file_info["chunk_count"],
                uploaded_at=datetime.fromisoformat(file_info["uploaded_at"])
            )
        }

    except ValueError as e:
        # Remove file if processing failed
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """Delete a document from the knowledge base."""
    rag = get_rag_service()

    success = rag.delete_document(file_id)

    if not success:
        raise HTTPException(status_code=404, detail="File not found")

    return {"success": True}


@router.get("/stats")
async def get_stats():
    """Get knowledge base statistics."""
    rag = get_rag_service()
    return rag.get_stats()


@router.post("/search")
async def search_knowledge(query: dict):
    """Search the knowledge base."""
    search_query = query.get("query", "")
    if not search_query:
        raise HTTPException(status_code=400, detail="Query required")

    rag = get_rag_service()
    results = rag.search(search_query)

    return {
        "query": search_query,
        "results": results
    }
