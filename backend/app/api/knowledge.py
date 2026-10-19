from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_tenant
from backend.app.models.entities import KnowledgeChunk
from backend.app.services.crawler import validate_target_url
from backend.app.services.knowledge import (
    approve_knowledge_chunk,
    get_approved_knowledge,
    ingest_crawled_content,
    reject_knowledge_chunk,
)

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base & Scraper"])


class CrawlRequest(BaseModel):
    url: str
    page_title: Optional[str] = "Website Homepage"
    simulated_content: Optional[str] = None  # Allows manual body or simulated payload


@router.post("/crawl")
def submit_crawl(
    req: CrawlRequest,
    org_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    valid, msg, domain = validate_target_url(req.url)
    if not valid:
        raise HTTPException(status_code=400, detail=f"SSRF Protection: {msg}")

    # Use simulated content if provided (for offline tests), else fetch real page content
    if req.simulated_content:
        content = req.simulated_content
        page_title = req.page_title or domain or "Page"
    else:
        import re
        from backend.app.services.crawler import fetch_url_safely
        success, fetched_html, final_url = fetch_url_safely(req.url, timeout=12.0)
        if not success:
            raise HTTPException(status_code=422, detail=f"Failed to crawl website: {fetched_html}")
        content = fetched_html
        title_m = re.search(r'(?is)<title[^>]*>(.*?)</title>', content)
        page_title = title_m.group(1).strip() if title_m else (req.page_title or domain or "Page")

    result = ingest_crawled_content(
        db=db,
        organization_id=org_id,
        url=req.url,
        page_title=page_title,
        raw_content=content,
        is_html=True
    )
    return result


@router.get("/chunks")
def list_chunks(
    status: Optional[str] = None,
    org_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    query = db.query(KnowledgeChunk).filter(KnowledgeChunk.organization_id == org_id)
    if status:
        query = query.filter(KnowledgeChunk.status == status)
    chunks = query.order_by(KnowledgeChunk.created_at.desc()).all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "fact_text": c.fact_text,
            "status": c.status,
            "created_at": c.created_at.isoformat()
        }
        for c in chunks
    ]


@router.post("/chunks/{chunk_id}/approve")
def approve_chunk_api(
    chunk_id: str,
    org_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    chunk = approve_knowledge_chunk(db, org_id, chunk_id)
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return {"id": chunk.id, "status": chunk.status}


@router.post("/chunks/{chunk_id}/reject")
def reject_chunk_api(
    chunk_id: str,
    org_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    chunk = reject_knowledge_chunk(db, org_id, chunk_id)
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return {"id": chunk.id, "status": chunk.status}
