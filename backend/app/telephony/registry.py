from typing import Any, Dict, Optional
from backend.app.telephony.base import TelephonyProvider
from backend.app.telephony.mock_adapter import MockTelephonyAdapter
from backend.app.telephony.sarvam_vobiz import SarvamVobizAdapter
from backend.app.telephony.exotel import ExotelAdapter
from backend.app.telephony.smartflo import SmartfloAdapter

_PROVIDER_MAP = {
    "mock": MockTelephonyAdapter,
    "sarvam_vobiz": SarvamVobizAdapter,
    "exotel": ExotelAdapter,
    "smartflo": SmartfloAdapter,
}


def get_telephony_provider(
    provider_type: str,
    credentials: Optional[Dict[str, Any]] = None
) -> TelephonyProvider:
    """Factory creating an instance of TelephonyProvider based on provider_type."""
    provider_cls = _PROVIDER_MAP.get(provider_type.lower())
    if not provider_cls:
        raise ValueError(f"Unsupported telephony provider: {provider_type}. Supported: {list(_PROVIDER_MAP.keys())}")
    return provider_cls(credentials=credentials)
