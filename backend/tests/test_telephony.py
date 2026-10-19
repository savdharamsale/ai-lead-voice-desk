import pytest
from backend.app.telephony.base import OutboundCallRequest
from backend.app.telephony.registry import get_telephony_provider
from backend.app.telephony.mock_adapter import MockTelephonyAdapter
from backend.app.telephony.sarvam_vobiz import SarvamVobizAdapter
from backend.app.telephony.exotel import ExotelAdapter
from backend.app.telephony.smartflo import SmartfloAdapter


@pytest.mark.asyncio
async def test_mock_telephony_lifecycle():
    adapter = get_telephony_provider("mock")
    caps = adapter.get_capabilities()
    assert caps.provider_name == "mock"
    assert caps.supports_live_transfer is True
    assert caps.pulse_duration_seconds == 30

    # 1. Initiate Call
    req = OutboundCallRequest(
        tenant_id="tenant_taj",
        destination_phone="+919876543210",
        from_phone="+912211002200",
        agent_prompt="You are a hotel booking assistant.",
        webhook_url="https://api.desk.in/api/v1/telephony/webhooks/mock",
        language="hi-IN"
    )
    res = await adapter.initiate_call(req)
    assert res.success is True
    assert res.provider_call_sid.startswith("mock_sid_")
    assert res.status == "initiated"

    # 2. Live Transfer
    transfer_res = await adapter.transfer_call(res.provider_call_sid, "+919800011122")
    assert transfer_res.success is True
    assert transfer_res.transfer_type == "live_bridge"

    # 3. Webhook Parsing
    webhook_payload = {
        "call_sid": res.provider_call_sid,
        "status": "completed",
        "duration": 52,
        "summary": "Customer confirmed booking for 150 guests."
    }
    event = await adapter.parse_webhook(webhook_payload, {})
    assert event.provider_call_sid == res.provider_call_sid
    assert event.status == "completed"
    assert event.duration_seconds == 52
    assert len(event.transcript) > 0


@pytest.mark.asyncio
async def test_sarvam_vobiz_capabilities_and_transfer():
    adapter = get_telephony_provider("sarvam_vobiz", credentials={"sarvam_api_key": "mock_test_key"})
    caps = adapter.get_capabilities()
    assert caps.provider_name == "sarvam_vobiz"
    assert caps.supports_live_transfer is True  # Verified in Sarvam documentation
    assert caps.indicative_rate_per_pulse_inr == 0.20

    transfer = await adapter.transfer_call("sv_call_123", "+919811223344")
    assert transfer.success is True
    assert transfer.transfer_type == "live_bridge"


@pytest.mark.asyncio
async def test_exotel_transfer_fallback():
    """Verifies that Exotel gracefully falls back to callback task creation."""
    adapter = get_telephony_provider("exotel", credentials={"api_key": "k", "account_sid": "s"})
    caps = adapter.get_capabilities()
    assert caps.supports_live_transfer is False  # Not self-serve in Sarvam

    transfer = await adapter.transfer_call("exo_call_123", "+919811223344")
    assert transfer.success is False
    assert transfer.transfer_type == "callback_fallback"
    assert "urgent callback task" in transfer.message


@pytest.mark.asyncio
async def test_smartflo_transfer_fallback():
    """Verifies that Tata Tele Smartflo gracefully falls back to callback task creation."""
    adapter = get_telephony_provider("smartflo", credentials={"api_key": "k", "api_secret": "s"})
    caps = adapter.get_capabilities()
    assert caps.supports_live_transfer is False

    transfer = await adapter.transfer_call("tt_call_123", "+919811223344")
    assert transfer.success is False
    assert transfer.transfer_type == "callback_fallback"
