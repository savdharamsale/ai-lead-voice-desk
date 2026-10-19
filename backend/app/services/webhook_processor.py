from datetime import datetime, timezone
import math
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.models.entities import (
    Call, CallEvent, CallSummary, Lead, Organization, Transcript, UsageEvent, WebhookEvent
)
from backend.app.services.consent import record_suppression
from backend.app.services.tasks import create_follow_up_task
from backend.app.telephony.registry import get_telephony_provider


async def process_telephony_webhook(
    db: Session,
    organization_id: str,
    provider_name: str,
    payload: Dict[str, Any],
    headers: Dict[str, str]
) -> Tuple[bool, str, Optional[Call]]:
    """Idempotently processes carrier webhooks, updates call state, calculates billing, and advances lead."""
    adapter = get_telephony_provider(provider_name)
    event = await adapter.parse_webhook(payload, headers)
    caps = adapter.get_capabilities()

    # 1. Idempotency Check
    existing_event = db.query(WebhookEvent).filter(
        WebhookEvent.organization_id == organization_id,
        WebhookEvent.provider_event_id == event.event_id
    ).first()
    if existing_event and existing_event.is_processed:
        # Return existing processed call
        call = db.query(Call).filter(
            Call.organization_id == organization_id,
            Call.provider_call_sid == event.provider_call_sid
        ).first()
        return True, "Event already processed (Idempotent replay)", call

    # Record Webhook Event
    webhook_rec = existing_event or WebhookEvent(
        organization_id=organization_id,
        provider_name=provider_name,
        provider_event_id=event.event_id,
        payload_json=payload,
        is_processed=False
    )
    if not existing_event:
        db.add(webhook_rec)
        db.flush()

    # 2. Locate Call Record
    call = db.query(Call).filter(
        Call.organization_id == organization_id,
        Call.provider_call_sid == event.provider_call_sid
    ).first()
    if not call:
        return False, f"Call SID {event.provider_call_sid} not found", None

    # 3. Update Call State & Duration
    call.status = event.status
    call.duration_seconds = event.duration_seconds
    if event.recording_url:
        call.recording_url = event.recording_url

    # 4. Calculate Usage & Cost
    # Pulse duration (default 30s)
    pulses = math.ceil(event.duration_seconds / caps.pulse_duration_seconds) if event.duration_seconds > 0 else 0
    telephony_cost = pulses * caps.indicative_rate_per_pulse_inr
    # Agent minutes (billed in whole 60s minutes)
    agent_mins = math.ceil(event.duration_seconds / 60) if event.duration_seconds > 0 else 0
    agent_cost = agent_mins * caps.indicative_agent_rate_per_min_inr
    total_cost = telephony_cost + agent_cost

    call.telephony_pulses_billed = pulses
    call.agent_minutes_billed = agent_mins
    call.cost_inr = round(total_cost, 2)

    # Update Organization monthly spend
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if org:
        org.current_month_spend_inr += call.cost_inr

    # Record Usage Events
    if total_cost > 0:
        usage = UsageEvent(
            organization_id=organization_id,
            event_type="voice_call",
            quantity=float(event.duration_seconds),
            unit_cost_inr=caps.indicative_rate_per_pulse_inr,
            total_cost_inr=call.cost_inr,
            reference_id=call.id
        )
        db.add(usage)

    # 5. Persist Transcript
    if event.transcript:
        full_dialogue = "\n".join([f"{t['speaker'].capitalize()}: {t['text']}" for t in event.transcript])
        transcript_obj = Transcript(
            organization_id=organization_id,
            call_id=call.id,
            raw_transcript_json=event.transcript,
            full_text=full_dialogue
        )
        db.add(transcript_obj)

    # 6. Persist Call Summary
    if event.summary or event.qualification_extracted:
        summary_obj = CallSummary(
            organization_id=organization_id,
            call_id=call.id,
            lead_id=call.lead_id,
            summary_text=event.summary or "Call completed",
            sentiment="positive" if event.qualification_extracted else "neutral",
            qualification_data_json=event.qualification_extracted,
            recommended_next_action="Send quotation & follow up"
        )
        db.add(summary_obj)

    # 7. Update Lead Pipeline Stage & Tasks
    lead = db.query(Lead).filter(
        Lead.organization_id == organization_id,
        Lead.id == call.lead_id
    ).first()

    if lead:
        # Check for opt-out in summary or qualification
        summary_lower = (event.summary or "").lower()
        if "opt out" in summary_lower or "do not call" in summary_lower or "stop" in summary_lower:
            record_suppression(db, organization_id, lead.phone, reason="Opt-out during voice call")
        elif event.qualification_extracted:
            lead.stage = "Qualified"
            # Auto-create follow-up task
            create_follow_up_task(
                db=db,
                organization_id=organization_id,
                title=f"High Priority: Follow up with {lead.first_name or 'Lead'} ({lead.phone})",
                description=f"AI Voice Agent qualified lead. Summary: {event.summary}",
                lead_id=lead.id,
                call_id=call.id,
                priority="high",
                due_in_hours=4
            )
        elif event.status == "completed":
            lead.stage = "Connected"
        elif event.status in ("busy", "no_answer", "failed"):
            lead.stage = "Attempted"

    webhook_rec.is_processed = True
    webhook_rec.processed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(call)
    return True, "Webhook processed successfully", call
