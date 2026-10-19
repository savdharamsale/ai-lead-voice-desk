import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.entities import ConsentEvent, Lead, SuppressionEntry

# Indian Standard Time (IST) is UTC+05:30
IST_OFFSET = timedelta(hours=5, minutes=30)
IST_TIMEZONE = timezone(IST_OFFSET, name="IST")


def normalize_indian_phone(phone_raw: str) -> Optional[str]:
    """Normalizes an Indian mobile phone number to E.164 format (+91XXXXXXXXXX)."""
    if not phone_raw:
        return None
    cleaned = re.sub(r"[^\d+]", "", phone_raw.strip())
    
    # Strip leading +91 or 91 or 0
    if cleaned.startswith("+91"):
        digits = cleaned[3:]
    elif cleaned.startswith("91") and len(cleaned) == 12:
        digits = cleaned[2:]
    elif cleaned.startswith("0") and len(cleaned) == 11:
        digits = cleaned[1:]
    else:
        digits = cleaned

    # Valid Indian mobile number is 10 digits starting with 6, 7, 8, or 9
    if len(digits) == 10 and digits[0] in "6789":
        return f"+91{digits}"
    return None


def is_within_calling_hours(dt: Optional[datetime] = None) -> Tuple[bool, str]:
    """Checks whether the given or current timestamp falls within TRAI allowed hours (09:00 - 21:00 IST)."""
    if not settings.ENFORCE_CALLING_HOURS:
        return True, "Calling hours enforcement disabled"

    now_utc = dt or datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(IST_TIMEZONE)
    current_hour = now_ist.hour
    
    if current_hour < settings.CALLING_WINDOW_START_HOUR or current_hour >= settings.CALLING_WINDOW_END_HOUR:
        return False, (
            f"TRAI Calling Hours Restriction: Outbound calls are prohibited between "
            f"{settings.CALLING_WINDOW_END_HOUR}:00 and {settings.CALLING_WINDOW_START_HOUR:02d}:00 IST. "
            f"Current time in IST: {now_ist.strftime('%H:%M:%S')}"
        )
    return True, f"Within allowed window ({now_ist.strftime('%H:%M:%S')} IST)"


def record_consent(
    db: Session,
    organization_id: str,
    lead_id: Optional[str],
    consent_type: str,
    consent_statement: str,
    channel: str,
    ip_address: Optional[str] = None
) -> ConsentEvent:
    """Records explicit consent provenance in the immutable audit ledger."""
    consent = ConsentEvent(
        organization_id=organization_id,
        lead_id=lead_id,
        consent_type=consent_type,
        consent_statement=consent_statement,
        channel=channel,
        ip_address=ip_address,
        consented_at=datetime.now(timezone.utc)
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    return consent


def record_suppression(
    db: Session,
    organization_id: str,
    phone_number: str,
    reason: str,
    source_channel: str = "call"
) -> SuppressionEntry:
    """Adds a phone number to the tenant suppression list and flags existing lead records."""
    norm_phone = normalize_indian_phone(phone_number) or phone_number
    existing = db.query(SuppressionEntry).filter(
        SuppressionEntry.organization_id == organization_id,
        SuppressionEntry.phone_number == norm_phone
    ).first()
    
    if not existing:
        entry = SuppressionEntry(
            organization_id=organization_id,
            phone_number=norm_phone,
            reason=reason,
            source_channel=source_channel,
            suppressed_at=datetime.now(timezone.utc)
        )
        db.add(entry)
        
    # Mark any matching lead as suppressed and update stage to Do Not Contact
    leads = db.query(Lead).filter(
        Lead.organization_id == organization_id,
        Lead.phone == norm_phone
    ).all()
    for l in leads:
        l.is_suppressed = True
        l.stage = "Do Not Contact"
        
    db.commit()
    return existing or entry


def is_suppressed(db: Session, organization_id: str, phone_number: str) -> bool:
    """Checks whether a phone number is registered in the tenant suppression list."""
    norm_phone = normalize_indian_phone(phone_number) or phone_number
    entry = db.query(SuppressionEntry).filter(
        SuppressionEntry.organization_id == organization_id,
        SuppressionEntry.phone_number == norm_phone
    ).first()
    return entry is not None


def validate_pre_dial_eligibility(
    db: Session,
    organization_id: str,
    phone_number: str,
    check_time: Optional[datetime] = None
) -> Tuple[bool, str]:
    """Performs mandatory pre-dial checks: calling hours, suppression, and E.164 validity."""
    norm_phone = normalize_indian_phone(phone_number)
    if not norm_phone:
        return False, f"Invalid Indian phone number: '{phone_number}'. Must be a 10-digit mobile number."

    # 1. Calling Hours Check (TRAI)
    allowed, msg = is_within_calling_hours(check_time)
    if not allowed:
        return False, msg

    # 2. Suppression / DND Check
    if is_suppressed(db, organization_id, norm_phone):
        return False, f"Phone number {norm_phone} is suppressed (Do Not Call / Opted Out)."

    return True, "Eligible to call"
