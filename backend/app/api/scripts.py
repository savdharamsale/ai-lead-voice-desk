from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_tenant
from backend.app.models.entities import Script
from backend.app.services.prompt_studio import INDUSTRY_TEMPLATES, approve_script, synthesize_voice_script

router = APIRouter(prefix="/scripts", tags=["Voice Scripts & Prompt Studio"])


class GenerateScriptRequest(BaseModel):
    industry_vertical: str  # hospitality, hospital_admin, food_catering, generic_b2b
    company_name: str
    language: str = "hi-IN"
    tone: str = "polite_professional"


@router.get("/templates")
def list_templates() -> Dict[str, Any]:
    return INDUSTRY_TEMPLATES


@router.get("")
def list_scripts(
    org_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    scripts = db.query(Script).filter(Script.organization_id == org_id).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "is_approved": s.is_approved,
            "content": s.content,
            "created_at": s.created_at.isoformat()
        }
        for s in scripts
    ]


@router.post("/generate")
def generate_draft(
    req: GenerateScriptRequest,
    org_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    script = synthesize_voice_script(
        db=db,
        organization_id=org_id,
        industry_vertical=req.industry_vertical,
        company_name=req.company_name,
        language=req.language,
        tone=req.tone
    )
    return {
        "id": script.id,
        "title": script.title,
        "is_approved": script.is_approved,
        "content": script.content
    }


@router.post("/{script_id}/approve")
def approve_script_endpoint(
    script_id: str,
    org_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    script = approve_script(db, org_id, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return {"id": script.id, "is_approved": script.is_approved}
