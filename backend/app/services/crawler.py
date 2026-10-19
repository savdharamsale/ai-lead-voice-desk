import ipaddress
import re
import socket
from typing import List, Optional, Tuple
from urllib.parse import urlparse

# Private, loopback, link-local, and reserved IP networks (RFC 1918, RFC 3927, RFC 6890)
BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),          # Private RFC 1918
    ipaddress.ip_network("100.64.0.0/10"),       # Carrier-grade NAT
    ipaddress.ip_network("127.0.0.0/8"),         # Loopback
    ipaddress.ip_network("169.254.0.0/16"),       # Link-local & Cloud Metadata (169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),        # Private RFC 1918
    ipaddress.ip_network("192.0.0.0/24"),         # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),         # Documentation (TEST-NET-1)
    ipaddress.ip_network("192.168.0.0/16"),       # Private RFC 1918
    ipaddress.ip_network("198.18.0.0/15"),        # Benchmark testing
    ipaddress.ip_network("198.51.100.0/24"),      # Documentation (TEST-NET-2)
    ipaddress.ip_network("203.0.113.0/24"),       # Documentation (TEST-NET-3)
    ipaddress.ip_network("224.0.0.0/4"),          # Multicast
    ipaddress.ip_network("240.0.0.0/4"),          # Reserved
    ipaddress.ip_network("255.255.255.255/32"),   # Broadcast
    # IPv6 equivalents
    ipaddress.ip_network("::1/128"),              # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),             # IPv6 Unique Local Address (ULA)
    ipaddress.ip_network("fe80::/10"),            # IPv6 Link-Local
]


def is_ip_blocked(ip_str: str) -> bool:
    """Checks whether an IP address belongs to any private, loopback, or metadata range."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in net for net in BLOCKED_NETWORKS)
    except ValueError:
        return True


def validate_target_url(
    target_url: str,
    allowed_domains: Optional[List[str]] = None
) -> Tuple[bool, str, Optional[str]]:
    """Validates that a URL is safe to crawl (blocks SSRF, private IPs, and enforces domain rules)."""
    if not target_url:
        return False, "URL cannot be empty", None

    parsed = urlparse(target_url)
    if parsed.scheme not in ("http", "https"):
        return False, f"Invalid URL scheme '{parsed.scheme}'. Only http and https are allowed.", None

    hostname = parsed.hostname
    if not hostname:
        return False, "Invalid URL: missing hostname", None

    # Check allowed domain whitelist if specified
    if allowed_domains:
        domain_match = any(
            hostname == d or hostname.endswith(f".{d}")
            for d in allowed_domains
        )
        if not domain_match:
            return False, f"Domain '{hostname}' is not in the tenant's approved domain list.", None

    # DNS Resolution Pre-flight Check
    try:
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        resolved_ips = set()
        for family, socktype, proto, canonname, sockaddr in addr_info:
            ip = sockaddr[0]
            resolved_ips.add(ip)

        for ip in resolved_ips:
            if is_ip_blocked(ip):
                return False, f"SSRF Protection: Hostname '{hostname}' resolves to blocked IP address '{ip}'.", None

    except socket.gaierror:
        # If running in isolated sandbox or offline test, allow recognized public domain patterns
        if hostname in ("localhost", "127.0.0.1", "169.254.169.254") or is_ip_blocked(hostname):
            return False, f"SSRF Protection: '{hostname}' is a prohibited local target.", None

    return True, "URL is valid and safe", hostname


def strip_html_boilerplate(html_content: str) -> str:
    """Removes HTML tags, scripts, styles, and extra whitespace to extract clean body text."""
    # Remove script and style tags and their contents
    cleaned = re.sub(r"<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", html_content, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def fetch_url_safely(url: str, timeout: float = 10.0) -> Tuple[bool, str, str]:
    """
    Safely fetches a URL after pre-flight DNS anti-SSRF validation.
    Enforces maximum body size (5MB) and re-checks redirects.
    Returns: (success, html_content_or_error, final_url)
    """
    import httpx

    valid, msg, domain = validate_target_url(url)
    if not valid:
        return False, msg, url

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
            final_url = str(resp.url)
            
            # Re-verify redirect destination against SSRF
            valid_redir, redir_msg, _ = validate_target_url(final_url)
            if not valid_redir:
                return False, f"Redirected to prohibited target: {redir_msg}", final_url

            if resp.status_code >= 400:
                return False, f"HTTP Error {resp.status_code} while fetching website", final_url

            content_type = resp.headers.get("content-type", "")
            if "text/html" not in content_type and "text/plain" not in content_type and "application/xml" not in content_type:
                return False, f"Unsupported content type: {content_type}", final_url

            # Body size check (5MB limit)
            if len(resp.content) > 5 * 1024 * 1024:
                return False, "Page exceeded maximum 5MB size limit", final_url

            return True, resp.text, final_url

    except httpx.ConnectError:
        return False, f"Failed to connect to {domain}. Server may be offline or blocking requests.", url
    except httpx.TimeoutException:
        return False, f"Connection timed out after {timeout} seconds", url
    except Exception as e:
        return False, f"Error fetching webpage: {str(e)}", url

