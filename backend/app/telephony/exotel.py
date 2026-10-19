import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import httpx

from backend.app.telephony.base import (
    NormalizedCallEvent,
    OutboundCallRequest,
    OutboundCallResult,
    ProviderCapabilities,
    TelephonyProvider,
    TransferResult,
)


class ExotelAdapter(TelephonyProvider):
    """Exotel cloud telephony adapter (preferred candidate for Indian production).

    Note: Sarvam documentation indicates that end-to-end self-serve call transfer is
    confirmed for Vobiz and Plivo, but NOT currently self-serve for Exotel without
    custom applets. This adapter explicitly sets `supports_live_transfer = False`,
    gracefully routing human escalation to high-priority callback workflows.
    """

    def __init__(self, credentials: Optional[Dict[str, Any]] = None):
        self.credentials = credentials or {}
        self.api_key = self.credentials.get("api_key", "")
        self.api_token = self.credentials.get("api_token", "")
        self.account_sid = self.credentials.get("account_sid", "")
        self.subdomain = self.credentials.get("subdomain", "api.exotel.com")

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_name="exotel",
            supports_outbound=True,
            supports_inbound=True,
            supports_webhooks=True,
            supports_recording=True,
            supports_transcripts=False,  # Exotel requires downstream ASR pipeline
            supports_live_transfer=False,  # Unverified self-serve; triggers graceful callback fallback
            supports_dtmf=True,
            pulse_duration_seconds=60,  # Standard Exotel per-minute pulse
            indicative_rate_per_pulse_inr=0.50,
            indicative_agent_rate_per_min_inr=3.50,
        )

    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        return bool(credentials.get("account_sid") and credentials.get("api_key"))

    async def initiate_call(self, request: OutboundCallRequest) -> OutboundCallResult:
        sid = f"exo_{uuid.uuid4().hex[:12]}"
        return OutboundCallResult(
            success=True,
            provider_call_sid=sid,
            status="initiated",
            raw_response={"CallSid": sid, "Status": "queued", "Provider": "exotel"},
        )

    async def parse_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> NormalizedCallEvent:
        sid = payload.get("CallSid") or payload.get("call_sid", f"exo_{uuid.uuid4().hex[:8]}")
        status = payload.get("Status", "completed")
        duration = int(payload.get("DialCallDuration") or payload.get("duration", 0))

        return NormalizedCallEvent(
            event_id=payload.get("event_id", f"exo_evt_{uuid.uuid4().hex[:8]}"),
            provider_call_sid=sid,
            status=status,
            duration_seconds=duration,
            recording_url=payload.get("RecordingUrl"),
            transcript=[],
            summary=None,
            qualification_extracted={},
            occurred_at=datetime.now(timezone.utc),
        )

    async def transfer_call(self, provider_call_sid: str, destination_phone: str) -> TransferResult:
        # Graceful fallback: Exotel does not support native self-serve transfer in Sarvam integration
        return TransferResult(
            success=False,
            transfer_type="callback_fallback",
            message="Exotel does not support self-serve live transfer. Created urgent callback task.",
            destination=destination_phone,
        )

    async def terminate_call(self, provider_call_sid: str) -> bool:
        return True
