import pytest
from backend.app.models.entities import Organization
from backend.app.services.crawler import is_ip_blocked, strip_html_boilerplate, validate_target_url
from backend.app.services.knowledge import (
    approve_knowledge_chunk,
    get_approved_knowledge,
    ingest_crawled_content,
)


def test_ssrf_ip_blocking():
    # Loopback
    assert is_ip_blocked("127.0.0.1") is True
    assert is_ip_blocked("127.0.1.5") is True
    # Cloud Metadata
    assert is_ip_blocked("169.254.169.254") is True
    # RFC 1918 Private ranges
    assert is_ip_blocked("10.0.0.1") is True
    assert is_ip_blocked("172.16.5.10") is True
    assert is_ip_blocked("192.168.1.1") is True
    # Public IPs should NOT be blocked
    assert is_ip_blocked("8.8.8.8") is False
    assert is_ip_blocked("1.1.1.1") is False


def test_url_validation_and_domain_whitelist():
    # Invalid schemes
    valid, msg, _ = validate_target_url("ftp://example.com/file")
    assert valid is False
    assert "scheme" in msg

    # Blocked localhost & metadata URLs
    valid, msg, _ = validate_target_url("http://localhost:8000/admin")
    assert valid is False

    valid, msg, _ = validate_target_url("http://127.0.0.1/status")
    assert valid is False

    valid, msg, _ = validate_target_url("http://169.254.169.254/latest/meta-data")
    assert valid is False

    # Domain whitelist
    allowed = ["tajhotels.com", "tajpalace.in"]
    valid, msg, domain = validate_target_url("https://unapproved-site.com/about", allowed_domains=allowed)
    assert valid is False
    assert "approved domain list" in msg


def test_html_boilerplate_stripping():
    html = """
    <html>
        <head><title>Test Hotel</title><style>body { color: red; }</style></head>
        <body>
            <nav><a href="/">Home</a><a href="/menu">Menu</a></nav>
            <h1>Welcome to The Grand Regal</h1>
            <p>We offer banquet halls for weddings up to 500 guests.</p>
            <footer>Copyright 2026 Grand Regal. All rights reserved.</footer>
            <script>alert("ignore script");</script>
        </body>
    </html>
    """
    cleaned = strip_html_boilerplate(html)
    assert "Welcome to The Grand Regal" in cleaned
    assert "banquet halls for weddings up to 500 guests" in cleaned
    assert "body { color: red; }" not in cleaned
    assert "ignore script" not in cleaned


def test_knowledge_draft_approval_gate(db):
    org = Organization(name="Grand Regal", slug="grand-regal")
    db.add(org)
    db.commit()

    sample_html = "<h1>Banquet Packages</h1><p>Our gold banquet package starts at 2500 per plate and includes 5-course dining.</p>"
    res = ingest_crawled_content(
        db=db,
        organization_id=org.id,
        url="https://grandregal.example/banquets",
        page_title="Banquet Pricing",
        raw_content=sample_html,
        is_html=True
    )
    assert res["chunks_created"] >= 1

    # 1. Before approval: Voice Agent should see 0 approved chunks
    approved_before = get_approved_knowledge(db, org.id)
    assert len(approved_before) == 0

    # 2. Query draft chunks
    from backend.app.models.entities import KnowledgeChunk
    draft_chunk = db.query(KnowledgeChunk).filter(
        KnowledgeChunk.organization_id == org.id,
        KnowledgeChunk.status == "draft"
    ).first()
    assert draft_chunk is not None

    # 3. Tenant Admin approves chunk
    approved_chunk = approve_knowledge_chunk(db, org.id, draft_chunk.id)
    assert approved_chunk.status == "approved"

    # 4. Now Voice Agent retrieves approved knowledge
    approved_after = get_approved_knowledge(db, org.id)
    assert len(approved_after) == 1
    assert "gold banquet package" in approved_after[0].fact_text
