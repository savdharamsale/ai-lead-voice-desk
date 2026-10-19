import pytest
from datetime import datetime, timezone
from backend.app.models.entities import Call, Lead, Organization, Task, UsageEvent
from backend.app.services.consent import IST_TIMEZONE
from backend.app.services.crm import create_lead
from backend.app.services.dispatcher import dispatch_outbound_call
from backend.app.services.prompt_studio import approve_script, synthesize_voice_script
from backend.app.services.webhook_processor import process_telephony_webhook


@pytest.mark.asyncio
async def test_complete_vertical_slice_lifecycle(db):
    """Executes the complete vertical slice:

    Tenant Onboard -> Lead Ingest -> Script Approval -> Call Dispatch ->
    Webhook Handling -> Cost Metering -> Lead Stage Qualification -> Task Spawn -> Idempotency.
    """
    # 1. Tenant Creation (The Grand Regal Hotel Mumbai)
    org = Organization(
        name="The Grand Regal Hotel",
        slug="grand-regal-mumbai",
        budget_cap_inr=5000.0,
        current_month_spend_inr=0.0
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    # 2. Ingest Lead with explicit consent
    lead, msg = create_lead(
        db=db,
        organization_id=org.id,
        first_name="Rohan",
        last_name="Mehta",
        phone="+919876543210",
        email="rohan.mehta@example.com",
        source="website_inquiry",
        consent_statement="Consented to event callback on 2026-10-19"
    )
    assert lead is not None
    assert lead.stage == "Eligible to Contact"
    assert lead.is_suppressed is False

    # 3. Create and Approve Voice Script
    script = synthesize_voice_script(
        db=db,
        organization_id=org.id,
        industry_vertical="hospitality",
        company_name="The Grand Regal Hotel",
        language="hi-IN"
    )
    assert script.is_approved is False

    # Attempting to dispatch before approval must be blocked
    success, reason, _ = await dispatch_outbound_call(
        db=db,
        organization_id=org.id,
        lead_id=lead.id,
        script_id=script.id,
        provider_name="mock"
    )
    assert success is False
    assert "must be reviewed and approved" in reason

    # Approve script
    approve_script(db, org.id, script.id)

    # 4. Dispatch Outbound Call
    # Ensure calling hours are active (simulate daytime 11:00 IST)
    success, reason, call = await dispatch_outbound_call(
        db=db,
        organization_id=org.id,
        lead_id=lead.id,
        script_id=script.id,
        provider_name="mock"
    )
    assert success is True
    assert call is not None
    assert call.status == "initiated"
    assert call.provider_call_sid.startswith("mock_sid_")

    # Verify Lead stage transitioned to "Attempted"
    db.refresh(lead)
    assert lead.stage == "Attempted"

    # 5. Process Provider Webhook Callback
    webhook_event_id = "evt_provider_991823"
    webhook_payload = {
        "event_id": webhook_event_id,
        "call_sid": call.provider_call_sid,
        "status": "completed",
        "duration": 52,  # 52 seconds -> 2 pulses (30s each) + 1 agent minute
        "summary": "Customer confirmed banquet inquiry for wedding reception with 200 guests on 15 Dec 2026.",
        "qualification_extracted": {
            "event_type": "Wedding Reception",
            "guest_count": 200,
            "target_date": "2026-12-15"
        },
        "recording_url": "https://storage.internal/rec_123.mp3"
    }

    ok, msg, updated_call = await process_telephony_webhook(
        db=db,
        organization_id=org.id,
        provider_name="mock",
        payload=webhook_payload,
        headers={}
    )
    assert ok is True
    assert updated_call.status == "completed"
    assert updated_call.duration_seconds == 52

    # 6. Verify Billing & Usage
    # 52 seconds / 30s = 2 pulses @ 0.20 = 0.40
    # 52 seconds / 60s = 1 minute @ 3.50 = 3.50
    # Total = 3.90 INR
    assert updated_call.telephony_pulses_billed == 2
    assert updated_call.agent_minutes_billed == 1
    assert updated_call.cost_inr == 3.90

    db.refresh(org)
    assert org.current_month_spend_inr == 3.90

    # 7. Verify Lead Progression to "Qualified"
    db.refresh(lead)
    assert lead.stage == "Qualified"

    # 8. Verify Follow-Up Task Spawning
    tasks = db.query(Task).filter(
        Task.organization_id == org.id,
        Task.lead_id == lead.id
    ).all()
    assert len(tasks) == 1
    task = tasks[0]
    assert task.priority == "high"
    assert "Follow up with Rohan" in task.title
    assert "wedding reception" in task.description.lower()

    # 9. Test Webhook Idempotency (Replay Attack / Duplicate Deliveries)
    replay_ok, replay_msg, replay_call = await process_telephony_webhook(
        db=db,
        organization_id=org.id,
        provider_name="mock",
        payload=webhook_payload,
        headers={}
    )
    assert replay_ok is True
    assert "Idempotent replay" in replay_msg

    # Verify no duplicate task was created
    tasks_after = db.query(Task).filter(Task.organization_id == org.id, Task.lead_id == lead.id).all()
    assert len(tasks_after) == 1

    # Verify no duplicate billing occurred
    db.refresh(org)
    assert org.current_month_spend_inr == 3.90
