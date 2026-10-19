import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any, Dict, Optional, Tuple
from backend.app.core.config import settings


def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2-HMAC-SHA256 with a unique random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored salt$hash format."""
    try:
        salt, stored_hash = hashed_password.split("$", 1)
        calculated_hash = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return hmac.compare_digest(calculated_hash.hex(), stored_hash)
    except Exception:
        return False


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding and padding < 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def create_access_token(payload: Dict[str, Any], expires_delta_seconds: Optional[int] = None) -> str:
    """Creates a signed JWT using HS256."""
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    exp = now + (expires_delta_seconds or (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60))
    token_claims = {**payload, "iat": now, "exp": exp}
    
    header_b64 = _b64_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64_encode(json.dumps(token_claims, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    
    signature = hmac.new(settings.SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64_encode(signature)
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates an HS256 JWT."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        
        expected_sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
        actual_sig = _b64_decode(sig_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
            
        claims = json.loads(_b64_decode(payload_b64).decode("utf-8"))
        if claims.get("exp") and claims["exp"] < int(time.time()):
            return None  # Token expired
        return claims
    except Exception:
        return None


def encrypt_credential(plain_text: str) -> str:
    """Symmetrically encrypts a sensitive credential using key derivation and HMAC verification."""
    key = hashlib.sha256(settings.ENCRYPTION_KEY.encode("utf-8")).digest()
    iv = secrets.token_bytes(16)
    
    # Keystream via CTR-style PBKDF2 stream
    data_bytes = plain_text.encode("utf-8")
    keystream = hashlib.sha256(key + iv).digest()
    while len(keystream) < len(data_bytes):
        keystream += hashlib.sha256(keystream + key).digest()
    
    cipher_bytes = bytes([b ^ k for b, k in zip(data_bytes, keystream[:len(data_bytes)])])
    mac = hmac.new(key, iv + cipher_bytes, hashlib.sha256).digest()
    
    packed = iv + mac + cipher_bytes
    return base64.b64encode(packed).decode("utf-8")


def decrypt_credential(cipher_text_b64: str) -> Optional[str]:
    """Decrypts and verifies ciphertext created by encrypt_credential."""
    try:
        raw = base64.b64decode(cipher_text_b64.encode("utf-8"))
        if len(raw) < 16 + 32:
            return None
        iv = raw[:16]
        mac = raw[16:48]
        cipher_bytes = raw[48:]
        
        key = hashlib.sha256(settings.ENCRYPTION_KEY.encode("utf-8")).digest()
        expected_mac = hmac.new(key, iv + cipher_bytes, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected_mac):
            return None
            
        keystream = hashlib.sha256(key + iv).digest()
        while len(keystream) < len(cipher_bytes):
            keystream += hashlib.sha256(keystream + key).digest()
            
        plain_bytes = bytes([b ^ k for b, k in zip(cipher_bytes, keystream[:len(cipher_bytes)])])
        return plain_bytes.decode("utf-8")
    except Exception:
        return None
