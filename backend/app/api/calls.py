from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_tenant
from backend.app.models.entities import Call, CallSummary, Lead, Transcript
from backend.app.services.dispatcher import dispatch_outbound_call

router = APIRouter(prefix="/calls", tags=["Voice Calling"])


class DispatchCallRequest(BaseModel):
    lead_id: str
    script_id: str
    phone_number_id: Optional[str] = None
    provider_name: str = "mock"


@router.get("")
def list_calls(
    org_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    calls = db.query(Call).filter(Call.organization_id == org_id).order_by(Call.created_at.desc()).all()
    results = []
    for c in calls:
        summary = db.query(CallSummary).filter(CallSummary.call_id == c.id).first()
        results.append({
            "id": c.id,
            "provider_call_sid": c.provider_call_sid,
            "provider_type": c.provider_type,
            "direction": c.direction,
            "status": c.status,
            "destination": c.destination,
            "duration_seconds": c.duration_seconds,
            "cost_inr": c.cost_inr,
            "summary": summary.summary_text if summary else None,
            "recording_url": c.recording_url,
            "created_at": c.created_at.isoformat()
        })
    return results


@router.post("/dispatch")
async def dispatch_call_endpoint(
    req: DispatchCallRequest,
    org_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    ok, msg, call = await dispatch_outbound_call(
        db=db,
        organization_id=org_id,
        lead_id=req.lead_id,
        script_id=req.script_id,
        phone_number_id=req.phone_number_id,
        provider_name=req.provider_name
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {
        "call_id": call.id,
        "provider_call_sid": call.provider_call_sid,
        "status": call.status,
        "message": msg
    }


@router.get("/{call_id}/transcript")
def get_call_transcript(
    call_id: str,
    org_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    transcript = db.query(Transcript).filter(
        Transcript.organization_id == org_id,
        Transcript.call_id == call_id
    ).first()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return {
        "call_id": transcript.call_id,
        "full_text": transcript.full_text,
        "dialogue": transcript.raw_transcript_json
    }
