import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from backend.app.telephony.base import (
    NormalizedCallEvent,
    OutboundCallRequest,
    OutboundCallResult,
    ProviderCapabilities,
    TelephonyProvider,
    TransferResult,
)


class MockTelephonyAdapter(TelephonyProvider):
    """In-memory stateful mock telephony adapter for automated tests, CI/CD, and offline development."""

    def __init__(self, credentials: Optional[Dict[str, Any]] = None):
        self.credentials = credentials or {}
        self.active_calls: Dict[str, Dict[str, Any]] = {}

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_name="mock",
            supports_outbound=True,
            supports_inbound=True,
            supports_webhooks=True,
            supports_recording=True,
            supports_transcripts=True,
            supports_live_transfer=True,
            supports_dtmf=True,
            pulse_duration_seconds=30,
            indicative_rate_per_pulse_inr=0.20,
            indicative_agent_rate_per_min_inr=3.50,
        )

    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        return True

    async def initiate_call(self, request: OutboundCallRequest) -> OutboundCallResult:
        sid = f"mock_sid_{uuid.uuid4().hex[:12]}"
        call_record = {
            "sid": sid,
            "tenant_id": request.tenant_id,
            "lead_id": request.lead_id,
            "destination": request.destination_phone,
            "status": "initiated",
            "created_at": datetime.now(timezone.utc),
            "language": request.language,
        }
        self.active_calls[sid] = call_record

        return OutboundCallResult(
            success=True,
            provider_call_sid=sid,
            status="initiated",
            raw_response={"mock_status": "queued", "call_sid": sid},
        )

    async def parse_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> NormalizedCallEvent:
        sid = payload.get("call_sid") or payload.get("provider_call_sid", f"mock_sid_{uuid.uuid4().hex[:8]}")
        status = payload.get("status", "completed")
        duration = payload.get("duration", 45)

        transcript = payload.get("transcript") or [
            {"speaker": "agent", "text": "नमस्ते, मैं होटल से बोल रहा हूँ। क्या आप बैंक्वेट हॉल की जानकारी चाहते हैं?"},
            {"speaker": "user", "text": "हाँ, मुझे 15 दिसंबर के लिए 200 लोगों की शादी का रिसेप्शन प्लान करना है।"},
            {"speaker": "agent", "text": "बहुत बढ़िया, मैंने विवरण नोट कर लिया है। हमारे इवेंट मैनेजर आपको कोटेशन भेजेंगे।"}
        ]

        summary = payload.get("summary") or "Customer inquired about banquet booking for wedding reception with 200 guests on 15 Dec. Requested quote."
        qualification = payload.get("qualification_extracted") or {
            "event_type": "Wedding Reception",
            "guest_count": 200,
            "target_date": "2026-12-15",
            "budget": "premium"
        }

        return NormalizedCallEvent(
            event_id=payload.get("event_id", f"evt_{uuid.uuid4().hex[:8]}"),
            provider_call_sid=sid,
            status=status,
            duration_seconds=duration,
            recording_url=payload.get("recording_url", f"https://mock-storage.internal/recordings/{sid}.mp3"),
            transcript=transcript,
            summary=summary,
            qualification_extracted=qualification,
            occurred_at=datetime.now(timezone.utc),
        )

    async def transfer_call(self, provider_call_sid: str, destination_phone: str) -> TransferResult:
        if provider_call_sid not in self.active_calls:
            return TransferResult(
                success=False,
                transfer_type="callback_fallback",
                message=f"Call {provider_call_sid} not active",
                destination=destination_phone,
            )

        self.active_calls[provider_call_sid]["status"] = "transferred"
        return TransferResult(
            success=True,
            transfer_type="live_bridge",
            message=f"Transferred live call {provider_call_sid} to {destination_phone}",
            destination=destination_phone,
        )

    async def terminate_call(self, provider_call_sid: str) -> bool:
        if provider_call_sid in self.active_calls:
            self.active_calls[provider_call_sid]["status"] = "terminated"
            return True
        return False
