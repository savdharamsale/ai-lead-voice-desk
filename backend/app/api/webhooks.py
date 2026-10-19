from typing import Any, Dict
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.entities import Call, Organization
from backend.app.services.webhook_processor import process_telephony_webhook

router = APIRouter(prefix="/telephony/webhooks", tags=["Telephony Webhooks"])


@router.post("/{provider_name}")
async def receive_carrier_webhook(
    provider_name: str,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Ingests provider status callbacks and normalizes call completion/transcripts."""
    payload = await request.json()
    headers = dict(request.headers)

    # Resolve organization from Call record via CallSid
    call_sid = (
        payload.get("call_sid") or
        payload.get("CallSid") or
        payload.get("provider_call_sid") or
        payload.get("call_id")
    )
    if not call_sid:
        raise HTTPException(status_code=400, detail="Missing call identifier in webhook payload")

    call = db.query(Call).filter(Call.provider_call_sid == call_sid).first()
    if not call:
        # If call record not found, accept for mock or return 404
        raise HTTPException(status_code=404, detail=f"Call {call_sid} not found")

    ok, msg, updated_call = await process_telephony_webhook(
        db=db,
        organization_id=call.organization_id,
        provider_name=provider_name,
        payload=payload,
        headers=headers
    )
    return {
        "status": "processed" if ok else "failed",
        "message": msg,
        "call_id": updated_call.id if updated_call else None
    }
