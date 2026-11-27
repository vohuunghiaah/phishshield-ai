"""Lexical features and offline Public Suffix List grouping."""

import ipaddress
import math
import re
from collections import Counter
from functools import lru_cache
from urllib.parse import parse_qsl, urlsplit

import tldextract

PSL = tldextract.TLDExtract(
    suffix_list_urls=(), cache_dir=None, include_psl_private_domains=True
)
KEYWORDS = (
    "login",
    "verify",
    "secure",
    "account",
    "password",
    "update",
    "bank",
    "signin",
)


@lru_cache(maxsize=32768)
def host_info(host):
    host = host.rstrip(".").encode("idna").decode("ascii").lower()
    try:
        return str(ipaddress.ip_address(host)), 0, True
    except ValueError:
        if (
            not host
            or len(host) > 253
            or not all(
                re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", x)
                for x in host.split(".")
            )
        ):
            raise ValueError("Tên miền không hợp lệ")
        ext = PSL(host)
        return (
            ext.top_domain_under_public_suffix or host,
            len(ext.subdomain.split(".")) if ext.subdomain else 0,
            False,
        )


def parse_url(url):
    if (
        not isinstance(url, str)
        or not url
        or any(c.isspace() or ord(c) < 32 for c in url)
        or "\\" in url
    ):
        raise ValueError("URL có khoảng trắng hoặc ký tự không hợp lệ")
    u = urlsplit(url)
    if u.scheme.lower() not in ("http", "https") or not u.hostname:
        raise ValueError("Cần URL HTTP(S) có hostname")
    _ = u.port
    host_info(u.hostname)
    return u


def url_features(url):
    u = parse_url(url)
    _, subs, ip = host_info(u.hostname)
    n = len(url)
    digits = sum(c.isdigit() for c in url)
    return dict(
        url_length=n,
        hostname_length=len(u.hostname),
        path_length=len(u.path),
        subdomain_count=subs,
        dot_count=url.count("."),
        hyphen_count=url.count("-"),
        digit_count=digits,
        digit_ratio=digits / n,
        special_count=sum(not c.isalnum() for c in url),
        query_count=len(parse_qsl(u.query, keep_blank_values=True)),
        https=int(u.scheme == "https"),
        ip_host=int(ip),
        keyword_count=sum(url.lower().count(k) for k in KEYWORDS),
        entropy=-sum((c / n) * math.log2(c / n) for c in Counter(url).values()),
        encoded_count=len(re.findall(r"%[a-fA-F0-9]{2}", url)),
        punycode=int(any(x.startswith("xn--") for x in u.hostname.lower().split("."))),
        explicit_port=int(u.port is not None),
    )
