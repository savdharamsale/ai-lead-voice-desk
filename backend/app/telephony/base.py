from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProviderCapabilities(BaseModel):
    provider_name: str
    supports_outbound: bool = True
    supports_inbound: bool = True
    supports_webhooks: bool = True
    supports_recording: bool = True
    supports_transcripts: bool = True
    supports_live_transfer: bool = False  # True only for Vobiz/Plivo in Sarvam docs
    supports_dtmf: bool = True
    pulse_duration_seconds: int = 30
    indicative_rate_per_pulse_inr: float = 0.20
    indicative_agent_rate_per_min_inr: float = 3.50


class OutboundCallRequest(BaseModel):
    tenant_id: str
    lead_id: Optional[str] = None
    destination_phone: str  # E.164: +91XXXXXXXXXX
    from_phone: str         # Configured virtual number
    agent_prompt: str
    webhook_url: str
    language: str = "hi-IN"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OutboundCallResult(BaseModel):
    success: bool
    provider_call_sid: str
    status: str  # queued, initiated, failed
    error_message: Optional[str] = None
    raw_response: Dict[str, Any] = Field(default_factory=dict)


class NormalizedCallEvent(BaseModel):
    event_id: str
    provider_call_sid: str
    status: str  # ringing, in_progress, completed, failed, busy, no_answer
    duration_seconds: int = 0
    recording_url: Optional[str] = None
    transcript: List[Dict[str, str]] = Field(default_factory=list)
    summary: Optional[str] = None
    qualification_extracted: Dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TransferResult(BaseModel):
    success: bool
    transfer_type: str  # live_bridge | callback_fallback
    message: str
    destination: str


class TelephonyProvider(ABC):
    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """Returns the declared capabilities and billing rates of this provider."""
        pass

    @abstractmethod
    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Validates provider credentials against the carrier API or sandbox."""
        pass

    @abstractmethod
    async def initiate_call(self, request: OutboundCallRequest) -> OutboundCallResult:
        """Initiates an outbound phone call through the provider."""
        pass

    @abstractmethod
    async def parse_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> NormalizedCallEvent:
        """Normalizes carrier-specific webhook payload into a canonical NormalizedCallEvent."""
        pass

    @abstractmethod
    async def transfer_call(self, provider_call_sid: str, destination_phone: str) -> TransferResult:
        """Transfers active call to a human agent, or initiates fallback if unsupported."""
        pass

    @abstractmethod
    async def terminate_call(self, provider_call_sid: str) -> bool:
        """Terminates an ongoing phone call."""
        pass
