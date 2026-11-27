"""Static snapshot parsing. No browser, entity fetches or embedded requests."""

from collections import Counter
from urllib.parse import urljoin, urlsplit
from lxml import etree
from phishshield.features.url_features import host_info, parse_url


def web_target(base, value):
    try:
        u = urlsplit(urljoin(base, value.strip()))
        if u.scheme in ("http", "https") and u.hostname:
            return host_info(u.hostname)[0]
    except (ValueError, UnicodeError):
        pass
    return None


def html_features(url, html):
    if not html.strip():
        raise ValueError("Snapshot rỗng")
    parser = etree.HTMLParser(no_network=True, recover=True, encoding="utf-8")
    doc = etree.fromstring(html.encode("utf8"), parser)
    if doc is None:
        raise ValueError("Snapshot không phân tích được")
    site = host_info(parse_url(url).hostname)[0]
    base = url
    bases = doc.xpath("(//base[@href])[1]/@href")
    if bases and web_target(url, bases[0]):
        base = urljoin(url, bases[0])
    tags = Counter(n.tag for n in doc.iter() if isinstance(n.tag, str))
    links = [web_target(base, a.get("href")) for a in doc.iter("a") if a.get("href")]
    links = [v for v in links if v]
    passwords = hidden = empty = external = suspicious = sensitive = 0
    for node in doc.iter("input"):
        typ = node.get("type", "").lower().strip()
        passwords += typ == "password"
        hidden += typ == "hidden"
        desc = " ".join(
            node.get(k, "") for k in ("type", "name", "id", "autocomplete")
        ).lower()
        sensitive |= int(
            any(
                w in desc
                for w in ("password", "passwd", "otp", "cc-number", "creditcard", "ssn")
            )
        )
    for form in doc.iter("form"):
        action = form.get("action", "").strip()
        target = web_target(base, action) if action else site
        cross = bool(target and target != site)
        external += cross
        empty += not action
        has_pwd = any(
            n.get("type", "").strip().lower() == "password" for n in form.iter("input")
        )
        suspicious += cross or (has_pwd and form.get("method", "get").lower() == "get")
    scripts = [
        web_target(base, n.get("src")) for n in doc.iter("script") if n.get("src")
    ]
    return dict(
        html_length=len(html),
        tag_count=sum(tags.values()),
        form_count=tags["form"],
        password_count=passwords,
        hidden_count=hidden,
        external_link_ratio=sum(t != site for t in links) / max(1, len(links)),
        external_action_count=external,
        iframe_count=tags["iframe"],
        script_count=tags["script"],
        external_script_count=sum(bool(t and t != site) for t in scripts),
        image_count=tags["img"],
        anchor_count=tags["a"],
        empty_action_count=empty,
        has_title=int(any("".join(t.itertext()).strip() for t in doc.iter("title"))),
        has_favicon=int(
            any("icon" in n.get("rel", "").lower().split() for n in doc.iter("link"))
        ),
        suspicious_form_count=suspicious,
        sensitive_input=int(sensitive),
    )
