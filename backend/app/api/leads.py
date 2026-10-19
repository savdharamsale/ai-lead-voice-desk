from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_tenant
from backend.app.models.entities import Lead
from backend.app.services.crm import create_lead, import_leads_csv, update_lead_stage

router = APIRouter(prefix="/leads", tags=["Leads CRM"])


class CreateLeadRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: str
    email: Optional[str] = None
    source: str = "manual"
    consent_statement: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None


class UpdateStageRequest(BaseModel):
    stage: str


@router.get("")
def list_leads(
    stage: Optional[str] = None,
    org_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    query = db.query(Lead).filter(Lead.organization_id == org_id)
    if stage:
        query = query.filter(Lead.stage == stage)
    leads = query.order_by(Lead.created_at.desc()).all()
    return [
        {
            "id": l.id,
            "first_name": l.first_name,
            "last_name": l.last_name,
            "phone": l.phone,
            "email": l.email,
            "stage": l.stage,
            "source": l.source,
            "is_suppressed": l.is_suppressed,
            "custom_fields": l.custom_fields,
            "created_at": l.created_at.isoformat()
        }
        for l in leads
    ]


@router.post("")
def add_lead(
    req: CreateLeadRequest,
    org_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    lead, msg = create_lead(
        db=db,
        organization_id=org_id,
        first_name=req.first_name,
        last_name=req.last_name,
        phone=req.phone,
        email=req.email,
        source=req.source,
        consent_statement=req.consent_statement,
        custom_fields=req.custom_fields
    )
    if not lead:
        raise HTTPException(status_code=400, detail=msg)
    return {
        "id": lead.id,
        "first_name": lead.first_name,
        "last_name": lead.last_name,
        "phone": lead.phone,
        "email": lead.email,
        "stage": lead.stage,
        "source": lead.source,
        "is_suppressed": lead.is_suppressed,
        "custom_fields": lead.custom_fields,
        "created_at": lead.created_at.isoformat(),
        "message": msg
    }


@router.patch("/{lead_id}/stage")
def change_lead_stage(
    lead_id: str,
    req: UpdateStageRequest,
    org_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    try:
        lead = update_lead_stage(db, org_id, lead_id, req.stage)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        return {"id": lead.id, "stage": lead.stage}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/import-csv")
async def import_csv(
    file: UploadFile = File(...),
    org_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    content = await file.read()
    csv_text = content.decode("utf-8")
    return import_leads_csv(db, org_id, csv_text)


class ExtractContactsRequest(BaseModel):
    url: str
    crawl_subpages: Optional[bool] = True


@router.post("/extract-contacts")
def extract_contacts_endpoint(
    req: ExtractContactsRequest,
    org_id: str = Depends(get_current_tenant)
) -> Dict[str, Any]:
    """
    Harvey-powered Contact & Lead Discovery.
    Crawls website, extracts phone numbers, email addresses, decision makers, and social links.
    """
    from backend.app.services.contact_extractor import extract_website_contacts
    return extract_website_contacts(req.url, crawl_subpages=req.crawl_subpages)


class ImportExtractedItem(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: str
    email: Optional[str] = None
    title: Optional[str] = None
    source_url: Optional[str] = None


class BatchImportExtractedRequest(BaseModel):
    contacts: List[ImportExtractedItem]
    consent_statement: Optional[str] = "Discovered via authorized business website profile"


@router.post("/import-extracted")
def import_extracted_contacts(
    req: BatchImportExtractedRequest,
    org_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Imports extracted contacts into CRM leads with deduplication and normalization."""
    imported = []
    skipped = []

    for item in req.contacts:
        lead, msg = create_lead(
            db=db,
            organization_id=org_id,
            first_name=item.first_name,
            last_name=item.last_name,
            phone=item.phone,
            email=item.email,
            source="harvey_extractor",
            consent_statement=req.consent_statement,
            custom_fields={"title": item.title, "source_url": item.source_url}
        )
        if lead:
            imported.append({"id": lead.id, "name": f"{lead.first_name or ''} {lead.last_name or ''}".strip(), "phone": lead.phone})
        else:
            skipped.append({"phone": item.phone, "reason": msg})

    return {
        "status": "success",
        "imported_count": len(imported),
        "skipped_count": len(skipped),
        "imported": imported,
        "skipped": skipped
    }

