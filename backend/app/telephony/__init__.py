from backend.app.telephony.base import (
    TelephonyProvider,
    ProviderCapabilities,
    OutboundCallRequest,
    OutboundCallResult,
    NormalizedCallEvent,
    TransferResult,
)
from backend.app.telephony.mock_adapter import MockTelephonyAdapter
from backend.app.telephony.sarvam_vobiz import SarvamVobizAdapter
from backend.app.telephony.exotel import ExotelAdapter
from backend.app.telephony.smartflo import SmartfloAdapter
from backend.app.telephony.registry import get_telephony_provider

__all__ = [
    "TelephonyProvider",
    "ProviderCapabilities",
    "OutboundCallRequest",
    "OutboundCallResult",
    "NormalizedCallEvent",
    "TransferResult",
    "MockTelephonyAdapter",
    "SarvamVobizAdapter",
    "ExotelAdapter",
    "SmartfloAdapter",
    "get_telephony_provider",
]
