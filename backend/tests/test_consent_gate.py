from datetime import datetime, timezone, timedelta
import pytest
from backend.app.models.entities import Organization
from backend.app.services.consent import (
    IST_TIMEZONE,
    is_within_calling_hours,
    normalize_indian_phone,
    record_suppression,
    validate_pre_dial_eligibility,
)
from backend.app.services.crm import create_lead, import_leads_csv, update_lead_stage


def test_indian_phone_normalization():
    assert normalize_indian_phone("9876543210") == "+919876543210"
    assert normalize_indian_phone("+91 98765 43210") == "+919876543210"
    assert normalize_indian_phone("09876543210") == "+919876543210"
    assert normalize_indian_phone("+919876543210") == "+919876543210"
    # Invalid numbers
    assert normalize_indian_phone("12345") is None
    assert normalize_indian_phone("5551234567") is None  # Does not start with 6, 7, 8, or 9


def test_calling_hours_enforcement():
    # 21:15 IST (9:15 PM) -> should be blocked
    night_ist = datetime(2026, 10, 19, 21, 15, tzinfo=IST_TIMEZONE)
    allowed, msg = is_within_calling_hours(night_ist)
    assert allowed is False
    assert "TRAI Calling Hours Restriction" in msg

    # 07:45 IST (7:45 AM) -> should be blocked
    early_morning_ist = datetime(2026, 10, 19, 7, 45, tzinfo=IST_TIMEZONE)
    allowed, msg = is_within_calling_hours(early_morning_ist)
    assert allowed is False

    # 14:30 IST (2:30 PM) -> should be permitted
    afternoon_ist = datetime(2026, 10, 19, 14, 30, tzinfo=IST_TIMEZONE)
    allowed, msg = is_within_calling_hours(afternoon_ist)
    assert allowed is True


def test_suppression_and_pre_dial_gate(db):
    org = Organization(name="Test Org", slug="test-org")
    db.add(org)
    db.commit()

    phone = "+919876543210"
    # Permitted during daytime
    daytime_ist = datetime(2026, 10, 19, 11, 0, tzinfo=IST_TIMEZONE)
    eligible, msg = validate_pre_dial_eligibility(db, org.id, phone, check_time=daytime_ist)
    assert eligible is True

    # Suppress the number
    record_suppression(db, org.id, phone, reason="Customer requested DND")
    
    # Now dialing must be blocked
    eligible_after, msg_after = validate_pre_dial_eligibility(db, org.id, phone, check_time=daytime_ist)
    assert eligible_after is False
    assert "suppressed" in msg_after


def test_csv_import_with_deduplication_and_suppression(db):
    org = Organization(name="Taj Hotels", slug="taj-hotels")
    db.add(org)
    db.commit()

    # Pre-suppress one number
    record_suppression(db, org.id, "+919999999999", reason="opt_out")

    csv_data = """name,phone,email,consent
Amit Kumar,9876500001,amit@test.com,Web form consent on 19 Oct
Rohit Verma,9876500002,rohit@test.com,Consent granted via ad
Suppressed User,9999999999,supp@test.com,Old consent
Amit Duplicate,9876500001,amit@test.com,Duplicate phone
Invalid User,12345,,No phone
"""
    result = import_leads_csv(db, org.id, csv_data)
    assert result["imported_count"] == 3
    assert result["duplicate_count"] == 1
    assert result["suppressed_count"] == 1
    assert result["invalid_phone_count"] == 1
