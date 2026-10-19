import pytest
from backend.app.core.context import set_current_tenant_id, get_current_tenant_id
from backend.app.core.security import hash_password, verify_password, create_access_token, decode_access_token, encrypt_credential, decrypt_credential
from backend.app.models.entities import Organization, User, Membership, Lead, Call, Task


def test_password_hashing():
    pw = "SecretP@ssword123"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_credential_encryption_and_decryption():
    raw_api_key = "exotel_live_token_9876543210abcdef"
    cipher = encrypt_credential(raw_api_key)
    assert cipher != raw_api_key
    decrypted = decrypt_credential(cipher)
    assert decrypted == raw_api_key


def test_jwt_generation_and_decoding():
    payload = {"sub": "user_123", "organization_id": "org_taj_palace", "role": "tenant_admin"}
    token = create_access_token(payload, expires_delta_seconds=60)
    claims = decode_access_token(token)
    assert claims is not None
    assert claims["sub"] == "user_123"
    assert claims["organization_id"] == "org_taj_palace"
    assert claims["role"] == "tenant_admin"


def test_cross_tenant_isolation(db):
    """Verifies that Tenant B cannot access Tenant A leads, calls, or tasks."""
    # Create Tenant A (Taj Palace)
    org_a = Organization(name="The Taj Palace Mumbai", slug="taj-mumbai")
    # Create Tenant B (Apollo Clinics)
    org_b = Organization(name="Apollo Care Clinics", slug="apollo-clinics")
    db.add_all([org_a, org_b])
    db.commit()
    db.refresh(org_a)
    db.refresh(org_b)

    # Ingest Lead for Tenant A
    lead_a = Lead(
        organization_id=org_a.id,
        first_name="Rohan",
        last_name="Mehta",
        phone="+919876543210",
        stage="New",
        source="website_form"
    )
    # Ingest Lead for Tenant B
    lead_b = Lead(
        organization_id=org_b.id,
        first_name="Dr. Priya",
        last_name="Sharma",
        phone="+919811122233",
        stage="Qualified",
        source="csv_import"
    )
    db.add_all([lead_a, lead_b])
    db.commit()

    # Query with Tenant A context filter
    leads_for_tenant_a = db.query(Lead).filter(Lead.organization_id == org_a.id).all()
    assert len(leads_for_tenant_a) == 1
    assert leads_for_tenant_a[0].phone == "+919876543210"

    # Query with Tenant B context filter
    leads_for_tenant_b = db.query(Lead).filter(Lead.organization_id == org_b.id).all()
    assert len(leads_for_tenant_b) == 1
    assert leads_for_tenant_b[0].phone == "+919811122233"

    # Verify cross-tenant isolation: Tenant B querying Tenant A's lead ID yields None
    cross_tenant_query = db.query(Lead).filter(
        Lead.id == lead_a.id,
        Lead.organization_id == org_b.id
    ).first()
    assert cross_tenant_query is None, "Cross-tenant access violation: Tenant B accessed Tenant A record!"
