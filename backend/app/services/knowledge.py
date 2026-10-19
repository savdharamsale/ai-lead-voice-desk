from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.entities import CrawledPage, KnowledgeChunk, KnowledgeDocument
from backend.app.services.crawler import strip_html_boilerplate


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """Splits long text into overlapping chunks suitable for voice agent prompt injection."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk.strip())
        i += chunk_size - overlap
    return chunks


def ingest_crawled_content(
    db: Session,
    organization_id: str,
    url: str,
    page_title: str,
    raw_content: str,
    is_html: bool = True
) -> Dict[str, Any]:
    """Ingests raw page content, strips boilerplate, creates draft chunks for human review."""
    cleaned_text = strip_html_boilerplate(raw_content) if is_html else raw_content.strip()

    crawled_page = CrawledPage(
        organization_id=organization_id,
        url=url,
        status="completed",
        http_status=200,
        page_title=page_title,
        text_content=cleaned_text,
        crawled_at=datetime.now(timezone.utc),
    )
    db.add(crawled_page)
    db.flush()

    chunks = chunk_text(cleaned_text, chunk_size=300)
    created_chunks = []
    for idx, c_text in enumerate(chunks):
        title = f"{page_title or 'Page'} - Fact Chunk {idx + 1}"
        chunk_obj = KnowledgeChunk(
            organization_id=organization_id,
            crawled_page_id=crawled_page.id,
            chunk_index=idx,
            title=title,
            fact_text=c_text,
            status="draft",  # Mandatory: Draft until explicitly reviewed and approved
        )
        db.add(chunk_obj)
        created_chunks.append(chunk_obj)

    db.commit()
    return {
        "crawled_page_id": crawled_page.id,
        "url": url,
        "chunks_created": len(created_chunks),
        "status": "pending_human_review",
    }


def approve_knowledge_chunk(db: Session, organization_id: str, chunk_id: str) -> Optional[KnowledgeChunk]:
    """Marks a draft chunk as approved, making it accessible to voice agent prompts."""
    chunk = db.query(KnowledgeChunk).filter(
        KnowledgeChunk.organization_id == organization_id,
        KnowledgeChunk.id == chunk_id,
    ).first()
    if chunk:
        chunk.status = "approved"
        db.commit()
        db.refresh(chunk)
    return chunk


def reject_knowledge_chunk(db: Session, organization_id: str, chunk_id: str) -> Optional[KnowledgeChunk]:
    """Marks a chunk as rejected."""
    chunk = db.query(KnowledgeChunk).filter(
        KnowledgeChunk.organization_id == organization_id,
        KnowledgeChunk.id == chunk_id,
    ).first()
    if chunk:
        chunk.status = "rejected"
        db.commit()
        db.refresh(chunk)
    return chunk


def get_approved_knowledge(db: Session, organization_id: str) -> List[KnowledgeChunk]:
    """Retrieves ONLY tenant-approved knowledge chunks for prompt grounding."""
    return db.query(KnowledgeChunk).filter(
        KnowledgeChunk.organization_id == organization_id,
        KnowledgeChunk.status == "approved",
    ).order_by(KnowledgeChunk.created_at.desc()).all()
