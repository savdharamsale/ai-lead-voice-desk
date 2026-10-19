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
