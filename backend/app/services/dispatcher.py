from datetime import datetime, timezone
import math
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.models.entities import Call, Lead, Organization, PhoneNumber, Script, UsageEvent
from backend.app.services.consent import validate_pre_dial_eligibility
from backend.app.telephony.base import OutboundCallRequest
from backend.app.telephony.registry import get_telephony_provider


async def dispatch_outbound_call(
    db: Session,
    organization_id: str,
    lead_id: str,
    script_id: str,
    phone_number_id: Optional[str] = None,
    provider_name: str = "mock"
) -> Tuple[bool, str, Optional[Call]]:
    """Executes pre-flight gates and dispatches an outbound voice call for a lead."""
    # 1. Organization & Budget Check
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org or not org.is_active:
        return False, "Organization not found or inactive", None

    if org.current_month_spend_inr >= org.budget_cap_inr:
        return False, f"Tenant budget cap reached (₹{org.budget_cap_inr:.2f}). Dialing halted.", None

    # 2. Lead Validation
    lead = db.query(Lead).filter(
        Lead.organization_id == organization_id,
        Lead.id == lead_id
    ).first()
    if not lead:
        return False, f"Lead {lead_id} not found in this organization", None

    # 3. Regulatory & Consent Gate (TRAI quiet hours + suppression check)
    eligible, reason = validate_pre_dial_eligibility(db, organization_id, lead.phone)
    if not eligible:
        return False, f"Pre-dial gate blocked: {reason}", None

    # 4. Script Validation
    script = db.query(Script).filter(
        Script.organization_id == organization_id,
        Script.id == script_id
    ).first()
    if not script:
        return False, "Script not found", None
    if not script.is_approved:
        return False, "Voice script must be reviewed and approved by tenant admin before dialing", None

    # 5. Caller Phone Number
    caller_phone = "+912211002200"
    if phone_number_id:
        num_obj = db.query(PhoneNumber).filter(
            PhoneNumber.organization_id == organization_id,
            PhoneNumber.id == phone_number_id
        ).first()
        if num_obj:
            caller_phone = num_obj.phone_number

    # 6. Telephony Adapter Dispatch
    adapter = get_telephony_provider(provider_name)
    req = OutboundCallRequest(
        tenant_id=organization_id,
        lead_id=lead.id,
        destination_phone=lead.phone,
        from_phone=caller_phone,
        agent_prompt=script.content,
        webhook_url=f"/api/v1/telephony/webhooks/{provider_name}",
        language="hi-IN"
    )

    result = await adapter.initiate_call(req)
    if not result.success:
        return False, f"Provider initiation failed: {result.error_message}", None

    # 7. Persist Call Record
    call = Call(
        organization_id=organization_id,
        lead_id=lead.id,
        phone_number_id=phone_number_id,
        provider_type=provider_name,
        provider_call_sid=result.provider_call_sid,
        direction="outbound",
        status="initiated",
        destination=lead.phone,
    )
    db.add(call)

    # 8. Update Lead Stage to "Attempted"
    lead.stage = "Attempted"

    db.commit()
    db.refresh(call)
    return True, "Call initiated successfully", call
