from typing import Any, Dict, List, Optional
import httpx
from backend.app.core.config import settings

SUPPORTED_SARVAM_LANGUAGES = {
    "hi-IN": "Hindi",
    "en-IN": "Indian English",
    "te-IN": "Telugu",
    "ta-IN": "Tamil",
    "kn-IN": "Kannada",
    "bn-IN": "Bengali",
    "gu-IN": "Gujarati",
    "mr-IN": "Marathi",
    "ml-IN": "Malayalam",
    "pa-IN": "Punjabi",
    "od-IN": "Odia"
}


class SarvamVoiceAgentClient:
    """Client for Sarvam AI Voice Agent creation, prompt configuration, and speech models."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.SARVAM_API_KEY
        self.base_url = (base_url or settings.SARVAM_BASE_URL).rstrip("/")

    def get_supported_languages(self) -> Dict[str, str]:
        return SUPPORTED_SARVAM_LANGUAGES

    async def create_voice_agent(
        self,
        agent_name: str,
        system_prompt: str,
        language_code: str = "hi-IN",
        voice_id: str = "meera",
        enable_transfer: bool = True
    ) -> Dict[str, Any]:
        """Creates or updates a voice agent configuration in Sarvam API."""
        if self.api_key.startswith("mock_") or not self.api_key:
            return {
                "agent_id": f"sarvam_ag_{agent_name.lower().replace(' ', '_')[:12]}",
                "name": agent_name,
                "language_code": language_code,
                "status": "ready",
                "voice": voice_id,
                "telephony_supported": True,
            }

        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "name": agent_name,
            "prompt": system_prompt,
            "language": language_code,
            "voice": voice_id,
            "tools": [{"type": "call_transfer"}] if enable_transfer else []
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(f"{self.base_url}/voice-agents", json=payload, headers=headers)
                if res.status_code in (200, 201):
                    return res.json()
                return {"error": f"Sarvam error HTTP {res.status_code}", "detail": res.text}
        except Exception as e:
            return {"error": "Connection failed", "detail": str(e)}
