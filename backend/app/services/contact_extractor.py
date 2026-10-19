"""
Autonomous Contact & Lead Extractor (Inspired by EthanPlusAI's Harvey).
Extracts phone numbers, email addresses, decision-maker profiles, social links,
and tech stack signals from business websites with anti-SSRF protections.
"""

from html import unescape as html_unescape
import re
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

from backend.app.services.consent import normalize_indian_phone
from backend.app.services.crawler import fetch_url_safely, validate_target_url


# Non-name words filter from Harvey to prevent navigation headings from becoming contacts
NON_NAME_WORDS = frozenset("""
service services repair repairs roofing roof roofs contractor contracting
commercial residential industrial storm damage restoration installation
history about contact quote quotes estimate estimates free request get call
learn more read view our their your team staff careers jobs home page site
company companies inc llc ltd corp group solutions systems partners
gallery projects reviews testimonials financing warranty insurance claims
maintenance inspection replacement gutters siding windows doors metal shingle
shingles tile flat emergency 24 hour hours today now new best top quality
privacy policy terms conditions sitemap blog news events why choose us
areas served locations location city county state north south east west
espanol menu skip navigation search close open toggle menu login signin
hospital clinic doctor opd department appointments packages pricing
""".split())

DECISION_MAKER_TITLES = (
    "owner", "founder", "co-founder", "president", "ceo", "principal",
    "partner", "general manager", "operations manager", "practice manager",
    "office manager", "marketing director", "marketing manager",
    "director", "managing director", "chief", "doctor", "dr.", "head of"
)

ROLE_HINT = re.compile(
    r"\b(owner|founder|president|ceo|cfo|coo|cto|principal|partner|manager|"
    r"director|supervisor|superintendent|foreman|estimator|specialist|"
    r"consultant|coordinator|representative|rep|sales|marketing|operations|"
    r"office|project|account|service|technician|installer|inspector|"
    r"vice president|vp|executive|lead|head of|chief|doctor|dr\b|physician|surgeon)\b", re.I
)

# Common Indian STD codes for major cities
MAJOR_STD_CODES = {"022", "011", "080", "044", "040", "033", "020", "079", "0120", "0124", "0141"}

BENIGN_ASSET_EXTS = (".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif", ".css", ".js", ".woff", ".woff2", ".ttf")
IGNORED_EMAIL_DOMAINS = {"example.com", "sentry.io", "wixpress.com", "domain.com", "yourdomain.com", "test.com", "email.com"}


def _strip_code(html: str) -> str:
    """Removes scripts, styles, and comments before text extraction."""
    html = re.sub(r"(?is)<script\b.*?</script>", " ", html)
    html = re.sub(r"(?is)<style\b.*?</style>", " ", html)
    html = re.sub(r"(?s)<!--.*?-->", " ", html)
    return html


def extract_emails_from_html(html: str, domain: str = "") -> List[str]:
    """Extracts and validates clean email addresses from HTML."""
    emails: Set[str] = set()

    # 1. Mailto links
    for m in re.finditer(r'(?i)href=["\']mailto:([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', html):
        email = m.group(1).lower().strip()
        emails.add(email)

    # 2. General regex over text
    text_content = _strip_code(html)
    raw_matches = re.findall(r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b', text_content)
    for raw in raw_matches:
        e = raw.lower().strip(".,;:!'\"")
        # Filter out image/asset artifacts like logo@2x.png
        if any(e.endswith(ext) for ext in BENIGN_ASSET_EXTS):
            continue
        domain_part = e.split("@")[-1]
        if domain_part in IGNORED_EMAIL_DOMAINS:
            continue
        if len(e) < 5 or "." not in domain_part:
            continue
        emails.add(e)

    # Prioritize emails matching the website domain
    sorted_emails = sorted(
        list(emails),
        key=lambda x: (not (domain and domain in x), len(x))
    )
    return sorted_emails


def extract_phones_from_html(html: str) -> List[Dict[str, Any]]:
    """
    Extracts phone numbers (tel: links, WhatsApp links, and Indian mobile/landline regexes).
    Returns list of dicts with raw, normalized, and type fields.
    """
    results: List[Dict[str, Any]] = []
    seen_normalized: Set[str] = set()

    def add_phone(raw: str, label: str):
        cleaned = re.sub(r"[^\d+]", "", raw.strip())
        norm = normalize_indian_phone(cleaned)
        if norm and norm not in seen_normalized:
            seen_normalized.add(norm)
            results.append({
                "raw": raw.strip(),
                "normalized": norm,
                "type": label,
                "callable": True
            })

    # 1. Tel: links
    for m in re.finditer(r'(?i)href=["\']tel:([^"\']+)["\']', html):
        add_phone(m.group(1), "tel_link")

    # 2. WhatsApp links (wa.me/91XXXXXXXXXX or api.whatsapp.com)
    for m in re.finditer(r'(?i)(?:wa\.me|api\.whatsapp\.com/send\?phone=)[/]?(\+?\d{10,13})', html):
        add_phone(m.group(1), "whatsapp")

    # 3. Indian Mobile Numbers (starts with 6-9, 10 digits)
    text = _strip_code(html)
    for m in re.finditer(r'(?:\+?91[\s\-]?)?([6-9]\d{4}[\s\-]?\d{5})\b', text):
        add_phone(m.group(0), "mobile")

    # 4. Indian Landlines with STD codes (e.g. 022-67890001, 080 45678901)
    for m in re.finditer(r'\b(0\d{2,4}[\s\-]?\d{6,8})\b', text):
        raw = m.group(1)
        add_phone(raw, "landline")

    # 5. Toll Free numbers (1800 XXXXXX)
    for m in re.finditer(r'\b(1800[\s\-]?\d{3,4}[\s\-]?\d{3,4})\b', text):
        raw = m.group(1)
        cleaned = re.sub(r"[^\d]", "", raw)
        if cleaned not in seen_normalized:
            seen_normalized.add(cleaned)
            results.append({
                "raw": raw,
                "normalized": cleaned,
                "type": "toll_free",
                "callable": True
            })

    return results


def extract_people_from_html(html: str, domain: str = "") -> List[Dict[str, Any]]:
    """
    Extracts team members, executives, and decision makers from HTML using Harvey's algorithm.
    Predicts corporate emails using pattern builder ({f}.{l}@domain).
    """
    clean_html = _strip_code(html)
    people = []
    seen = set()

    for m in re.finditer(
        r"(?is)<(h[1-5]|strong|b)[^>]*>\s*([A-Z][a-z'\-]+(?:\s+[A-Z]\.?)?\s+"
        r"[A-Z][a-zA-Z'\-]+)\s*</\1>(?=(.{0,220}))", clean_html
    ):
        name = re.sub(r"\s+", " ", m.group(2)).strip()
        raw_after = m.group(3)
        nxt = re.search(r"(?i)<(h[1-5]|strong|b)\b", raw_after)
        if nxt:
            raw_after = raw_after[:nxt.start()]
        after = html_unescape(re.sub(r"(?s)<[^>]+>", " ", raw_after))
        after = re.sub(r"\s+", " ", after).strip()

        if name.lower() in seen or len(name) > 45 or len(name) < 4:
            continue
        if re.search(r"\d|@|\bthe\b|\bour\b|\bwe\b", name, re.I):
            continue

        tokens = [t.strip(".,'-").lower() for t in name.split()]
        if any(t in NON_NAME_WORDS for t in tokens):
            continue

        # Look for role in context
        is_dm = any(t in after.lower() for t in DECISION_MAKER_TITLES)
        has_role = bool(ROLE_HINT.search(after[:160]))
        if not has_role and not is_dm:
            continue

        title = ""
        low = after.lower()
        for t in DECISION_MAKER_TITLES:
            if t in low:
                idx = low.index(t)
                title = after[idx:idx + 60].strip(" ,.|-—·")
                break
        if not title:
            m2 = re.match(r"[\s,|\-–—·]*([A-Za-z][A-Za-z /&'\-]{2,45})", after)
            if m2:
                title = m2.group(1).strip()

        seen.add(name.lower())
        parts = name.split()
        first_name = parts[0]
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        # Harvey pattern generation
        f_clean = re.sub(r"[^a-z]", "", first_name.lower())
        l_clean = re.sub(r"[^a-z]", "", last_name.lower()) if last_name else ""
        predicted_email = ""
        if domain and f_clean and l_clean:
            predicted_email = f"{f_clean}.{l_clean}@{domain}"
        elif domain and f_clean:
            predicted_email = f"{f_clean}@{domain}"

        people.append({
            "name": name,
            "first_name": first_name,
            "last_name": last_name,
            "title": title[:80] or "Executive",
            "is_decision_maker": is_dm,
            "predicted_email": predicted_email
        })
        if len(people) >= 10:
            break

    return people


def extract_social_links(html: str) -> Dict[str, str]:
    """Finds social profile links (LinkedIn, Instagram, Facebook, X, YouTube, WhatsApp)."""
    socials = {}
    for link in re.finditer(r'(?i)href=["\'](https?://[^"\']+)["\']', html):
        href = link.group(1)
        if "linkedin.com/company" in href or "linkedin.com/in" in href:
            socials.setdefault("linkedin", href)
        elif "instagram.com" in href and not any(x in href for x in ("/p/", "/reel/")):
            socials.setdefault("instagram", href)
        elif "facebook.com" in href:
            socials.setdefault("facebook", href)
        elif "twitter.com" in href or "x.com" in href:
            socials.setdefault("twitter", href)
        elif "youtube.com" in href:
            socials.setdefault("youtube", href)
        elif "wa.me/" in href or "api.whatsapp.com" in href:
            socials.setdefault("whatsapp", href)
    return socials


def detect_tech_stack(html: str) -> List[str]:
    """Detects website platform and web tooling fingerprints."""
    tech = []
    checks = {
        "WordPress": (r"wp-content/", r"wp-includes/"),
        "Shopify": (r"cdn\.shopify\.com", r"myshopify\.com"),
        "Wix": (r"static\.parastorage\.com",),
        "Webflow": (r"assets\.website-files\.com", r"data-wf-domain"),
        "Google Analytics": (r"googletagmanager\.com/gtag", r"google-analytics\.com"),
        "Meta Pixel": (r"connect\.facebook\.net/.*fbevents\.js", r"fbq\s*\("),
        "WhatsApp Click-to-Chat": (r"wa\.me", r"api\.whatsapp\.com", r"whatsapp-widget"),
        "Calendly Booking": (r"assets\.calendly\.com", r"calendly\.com"),
        "Razorpay Payments": (r"checkout\.razorpay\.com",),
        "Stripe Payments": (r"js\.stripe\.com",)
    }
    for name, patterns in checks.items():
        if any(re.search(p, html, re.I) for p in patterns):
            tech.append(name)
    return sorted(tech)


def extract_website_contacts(target_url: str, crawl_subpages: bool = True) -> Dict[str, Any]:
    """
    Main extraction pipeline.
    Crawls homepage and discovered /contact or /about pages safely,
    aggregates phone numbers, emails, decision makers, tech stack, and social profiles.
    """
    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        target_url = f"https://{target_url}"

    success, html, final_url = fetch_url_safely(target_url, timeout=12.0)
    if not success:
        # Try http fallback if https failed
        if target_url.startswith("https://"):
            http_fallback = target_url.replace("https://", "http://", 1)
            success_http, html_http, final_url_http = fetch_url_safely(http_fallback, timeout=8.0)
            if success_http:
                success, html, final_url = success_http, html_http, final_url_http

    if not success:
        return {
            "success": False,
            "url": target_url,
            "error": html,
            "phones": [],
            "emails": [],
            "people": [],
            "socials": {},
            "tech_stack": [],
            "pages_crawled": []
        }

    parsed = urlparse(final_url)
    domain = parsed.netloc.lower().replace("www.", "")
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    pages_crawled = [final_url]
    combined_html = html

    # If subpage crawling enabled, fetch contact or about pages
    if crawl_subpages:
        candidate_paths = [
            "/contact", "/contact-us", "/reach-us",
            "/about", "/about-us", "/team", "/our-team"
        ]
        for path in candidate_paths[:3]:  # Limit to 3 candidate pages
            sub_url = urljoin(base_url, path)
            sub_ok, sub_html, sub_final = fetch_url_safely(sub_url, timeout=6.0)
            if sub_ok and len(sub_html) > 500:
                pages_crawled.append(sub_final)
                combined_html += "\n" + sub_html

    # Extract all signals
    phones = extract_phones_from_html(combined_html)
    emails = extract_emails_from_html(combined_html, domain=domain)
    people = extract_people_from_html(combined_html, domain=domain)
    socials = extract_social_links(combined_html)
    tech_stack = detect_tech_stack(combined_html)

    # Derive company name from title or domain
    title_m = re.search(r'(?is)<title[^>]*>(.*?)</title>', html)
    raw_title = title_m.group(1).strip() if title_m else ""
    cleaned_title = re.sub(r'[\-|\|•].*$', '', raw_title).strip() or domain.title()

    return {
        "success": True,
        "url": final_url,
        "domain": domain,
        "company_name": cleaned_title[:60],
        "phones": phones,
        "emails": emails,
        "people": people,
        "socials": socials,
        "tech_stack": tech_stack,
        "pages_crawled": pages_crawled,
        "summary": f"Discovered {len(phones)} phone(s), {len(emails)} email(s), and {len(people)} team member(s)."
    }
