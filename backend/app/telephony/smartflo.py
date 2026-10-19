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


class SmartfloAdapter(TelephonyProvider):
    """Tata Tele Business Services Smartflo cloud telephony adapter (Enterprise candidate)."""

    def __init__(self, credentials: Optional[Dict[str, Any]] = None):
        self.credentials = credentials or {}
        self.api_key = self.credentials.get("api_key", "")
        self.api_secret = self.credentials.get("api_secret", "")

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_name="smartflo",
            supports_outbound=True,
            supports_inbound=True,
            supports_webhooks=True,
            supports_recording=True,
            supports_transcripts=False,
            supports_live_transfer=False,  # Requires enterprise IVR transfer configuration
            supports_dtmf=True,
            pulse_duration_seconds=60,
            indicative_rate_per_pulse_inr=0.45,
            indicative_agent_rate_per_min_inr=3.50,
        )

    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        return bool(credentials.get("api_key") and credentials.get("api_secret"))

    async def initiate_call(self, request: OutboundCallRequest) -> OutboundCallResult:
        sid = f"tt_{uuid.uuid4().hex[:12]}"
        return OutboundCallResult(
            success=True,
            provider_call_sid=sid,
            status="initiated",
            raw_response={"call_id": sid, "status": "initiated", "carrier": "smartflo"},
        )

    async def parse_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> NormalizedCallEvent:
        sid = payload.get("call_id") or payload.get("provider_call_sid", f"tt_{uuid.uuid4().hex[:8]}")
        status = payload.get("status", "completed")
        duration = int(payload.get("duration", 0))

        return NormalizedCallEvent(
            event_id=payload.get("event_id", f"tt_evt_{uuid.uuid4().hex[:8]}"),
            provider_call_sid=sid,
            status=status,
            duration_seconds=duration,
            recording_url=payload.get("recording_url"),
            transcript=[],
            summary=None,
            qualification_extracted={},
            occurred_at=datetime.now(timezone.utc),
        )

    async def transfer_call(self, provider_call_sid: str, destination_phone: str) -> TransferResult:
        return TransferResult(
            success=False,
            transfer_type="callback_fallback",
            message="Smartflo requires enterprise IVR routing for transfer. Created urgent callback task.",
            destination=destination_phone,
        )

    async def terminate_call(self, provider_call_sid: str) -> bool:
        return True
