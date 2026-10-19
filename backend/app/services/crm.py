import csv
import io
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.models.entities import Lead, ConsentEvent, SuppressionEntry
from backend.app.services.consent import normalize_indian_phone, is_suppressed, record_consent

ALLOWED_STAGES = [
    "New",
    "Needs Review",
    "Eligible to Contact",
    "Queued",
    "Attempted",
    "Connected",
    "Qualified",
    "Follow-up",
    "Escalated",
    "Converted",
    "Not Interested",
    "Invalid",
    "Do Not Contact",
]


def create_lead(
    db: Session,
    organization_id: str,
    first_name: Optional[str],
    last_name: Optional[str],
    phone: str,
    email: Optional[str] = None,
    source: str = "manual",
    consent_statement: Optional[str] = None,
    custom_fields: Optional[Dict[str, Any]] = None
) -> Tuple[Optional[Lead], str]:
    """Creates a new lead with Indian phone validation and duplicate checking."""
    norm_phone = normalize_indian_phone(phone)
    if not norm_phone:
        return None, f"Invalid Indian phone number: '{phone}'"

    # Check for existing lead with same phone in tenant
    existing = db.query(Lead).filter(
        Lead.organization_id == organization_id,
        Lead.phone == norm_phone
    ).first()
    if existing:
        return existing, "Lead already exists with this phone number"

    suppressed = is_suppressed(db, organization_id, norm_phone)
    initial_stage = "Do Not Contact" if suppressed else ("Eligible to Contact" if consent_statement else "New")

    lead = Lead(
        organization_id=organization_id,
        first_name=first_name,
        last_name=last_name,
        phone=norm_phone,
        email=email,
        source=source,
        stage=initial_stage,
        is_suppressed=suppressed,
        custom_fields=custom_fields or {}
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    if consent_statement:
        record_consent(
            db=db,
            organization_id=organization_id,
            lead_id=lead.id,
            consent_type="explicit_opt_in",
            consent_statement=consent_statement,
            channel=source
        )

    return lead, "Created successfully"


def update_lead_stage(
    db: Session,
    organization_id: str,
    lead_id: str,
    new_stage: str
) -> Optional[Lead]:
    """Updates lead pipeline stage with validation."""
    if new_stage not in ALLOWED_STAGES:
        raise ValueError(f"Invalid stage '{new_stage}'. Allowed: {ALLOWED_STAGES}")

    lead = db.query(Lead).filter(
        Lead.organization_id == organization_id,
        Lead.id == lead_id
    ).first()
    if not lead:
        return None

    lead.stage = new_stage
    db.commit()
    db.refresh(lead)
    return lead


def import_leads_csv(
    db: Session,
    organization_id: str,
    csv_text: str,
    default_source: str = "csv_import",
    default_consent_statement: Optional[str] = None
) -> Dict[str, Any]:
    """Parses a CSV string and bulk imports leads with duplicate and suppression detection."""
    reader = csv.DictReader(io.StringIO(csv_text))
    
    total_rows = 0
    imported = 0
    duplicates = 0
    suppressed = 0
    invalid_phones = 0

    for row in reader:
        total_rows += 1
        phone_raw = row.get("phone") or row.get("Phone") or row.get("mobile") or row.get("Mobile")
        if not phone_raw:
            invalid_phones += 1
            continue

        norm_phone = normalize_indian_phone(phone_raw)
        if not norm_phone:
            invalid_phones += 1
            continue

        # Check existing
        existing = db.query(Lead).filter(
            Lead.organization_id == organization_id,
            Lead.phone == norm_phone
        ).first()
        if existing:
            duplicates += 1
            continue

        is_supp = is_suppressed(db, organization_id, norm_phone)
        if is_supp:
            suppressed += 1

        stage = "Do Not Contact" if is_supp else "Eligible to Contact"
        first_name = row.get("first_name") or row.get("name") or row.get("Name")
        last_name = row.get("last_name") or ""
        email = row.get("email") or row.get("Email")
        source = row.get("source") or default_source
        consent_stmt = row.get("consent") or default_consent_statement

        lead = Lead(
            organization_id=organization_id,
            first_name=first_name,
            last_name=last_name,
            phone=norm_phone,
            email=email,
            source=source,
            stage=stage,
            is_suppressed=is_supp,
            custom_fields={k: v for k, v in row.items() if k not in ["first_name", "last_name", "phone", "email", "source"]}
        )
        db.add(lead)
        db.flush()

        if consent_stmt:
            record_consent(
                db=db,
                organization_id=organization_id,
                lead_id=lead.id,
                consent_type="csv_declared_consent",
                consent_statement=consent_stmt,
                channel="csv_import"
            )

        imported += 1

    db.commit()
    return {
        "total_rows": total_rows,
        "imported_count": imported,
        "duplicate_count": duplicates,
        "suppressed_count": suppressed,
        "invalid_phone_count": invalid_phones,
    }
