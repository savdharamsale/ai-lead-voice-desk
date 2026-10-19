import pytest
from backend.app.services.contact_extractor import (
    extract_emails_from_html,
    extract_phones_from_html,
    extract_people_from_html,
    extract_social_links,
    detect_tech_stack,
    extract_website_contacts
)


SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>The Grand Imperial Hotel & Suites | Luxury Stays</title>
    <script src="https://www.googletagmanager.com/gtag/js?id=G-XXXXX"></script>
</head>
<body>
    <header>
        <a href="tel:+912267891234">Call Us: (022) 6789-1234</a>
        <a href="mailto:reservations@grandimperial.in">reservations@grandimperial.in</a>
    </header>
    
    <main>
        <h1>Welcome to Grand Imperial</h1>
        <p>Book banquets, rooms, and catering. Contact our mobile support at +91 98200 99887 or 9876543210.</p>
        <p>WhatsApp our concierge at <a href="https://wa.me/919820099887">Chat on WhatsApp</a>.</p>

        <section id="leadership">
            <h2>Meet Our Leadership</h2>
            <div class="team-card">
                <h3>Vikram Malhotra</h3>
                <p>Founder & Managing Director</p>
                <p>Vikram leads luxury hospitality operations across Western India.</p>
            </div>
            <div class="team-card">
                <h3>Pooja Sharma</h3>
                <p>General Manager of Banquets</p>
                <p>Specializes in 500+ pax corporate conferences.</p>
            </div>
            <div class="fake-card">
                <h3>Commercial Services</h3>
                <p>Learn more about our banquet halls.</p>
            </div>
        </section>
    </main>

    <footer>
        <a href="https://www.linkedin.com/company/grand-imperial">LinkedIn</a>
        <a href="https://www.instagram.com/grandimperial">Instagram</a>
        <p>Inquiries: info@grandimperial.in, billing@grandimperial.in</p>
    </footer>
</body>
</html>
"""


def test_phone_extraction():
    phones = extract_phones_from_html(SAMPLE_HTML)
    assert len(phones) >= 3
    normalized_numbers = [p["normalized"] for p in phones]
    
    # Check Indian mobile and landline
    assert "+912267891234" in normalized_numbers or "+919820099887" in normalized_numbers
    assert "+919876543210" in normalized_numbers


def test_email_extraction():
    emails = extract_emails_from_html(SAMPLE_HTML, domain="grandimperial.in")
    assert len(emails) >= 2
    assert "reservations@grandimperial.in" in emails
    assert "info@grandimperial.in" in emails


def test_harvey_people_extraction():
    people = extract_people_from_html(SAMPLE_HTML, domain="grandimperial.in")
    assert len(people) >= 2
    names = [p["name"] for p in people]
    
    # Real people with roles detected
    assert "Vikram Malhotra" in names
    assert "Pooja Sharma" in names
    
    # Non-name heading excluded
    assert "Commercial Services" not in names

    # Predicted emails generated
    vikram = next(p for p in people if p["name"] == "Vikram Malhotra")
    assert vikram["is_decision_maker"] is True
    assert vikram["predicted_email"] == "vikram.malhotra@grandimperial.in"


def test_social_and_tech_detection():
    socials = extract_social_links(SAMPLE_HTML)
    assert "linkedin" in socials
    assert "instagram" in socials

    tech = detect_tech_stack(SAMPLE_HTML)
    assert "Google Analytics" in tech
    assert "WhatsApp Click-to-Chat" in tech


def test_ssrf_protection_on_extract():
    res = extract_website_contacts("http://127.0.0.1:8000/internal-admin")
    assert res["success"] is False
    assert "SSRF" in res["error"] or "prohibited" in res["error"].lower() or "blocked" in res["error"].lower()
