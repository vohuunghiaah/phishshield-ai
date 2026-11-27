"""Opt-in static HTML retrieval through a trusted, externally isolated egress."""

import http.client
import re
import ipaddress
import socket
import ssl
from urllib.parse import quote, urljoin, urlunsplit
from phishshield.features.url_features import parse_url


class FetchPolicyError(ValueError):
    """A destination is outside the fetch policy."""


def resolve_public(u):
    if (
        u.username is not None
        or u.password is not None
        or u.port not in (None, 443 if u.scheme == "https" else 80)
    ):
        raise FetchPolicyError("Credentials or nonstandard port")
    host = u.hostname.encode("idna").decode()
    lower = host.lower().rstrip(".")
    if (
        "%" in host
        or lower.endswith(
            (".local", ".localhost", ".internal", ".localdomain", ".home.arpa")
        )
        or ("." not in lower and ":" not in lower)
    ):
        raise FetchPolicyError("Special host")
    answers = socket.getaddrinfo(
        host, u.port or (443 if u.scheme == "https" else 80), type=socket.SOCK_STREAM
    )
    for _, _, _, _, addr in answers:
        ip = ipaddress.ip_address(addr[0])
        if (
            not ip.is_global
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_loopback
            or ip.is_link_local
            or getattr(ip, "ipv4_mapped", None)
            or getattr(ip, "sixtofour", None)
            or getattr(ip, "teredo", None)
            or (ip.version == 6 and ip not in ipaddress.ip_network("2000::/3"))
        ):
            raise FetchPolicyError("Nonpublic address")
    if not answers:
        raise ValueError("DNS empty")
    for answer in answers:
        if answer[0] == socket.AF_INET:
            return host, answer
    raise ValueError("No supported public IPv4 address")


def fetch_inner(url, limit):
    for hop in range(4):
        if len(url) > 8192:
            raise FetchPolicyError("Location too long")
        try:
            u = parse_url(url)
        except (ValueError, UnicodeError) as exc:
            raise FetchPolicyError("Invalid location") from exc
        host, (family, kind, proto, _, addr) = resolve_public(u)
        with socket.socket(family, kind, proto) as raw:
            raw.settimeout(4)
            raw.connect(
                addr
            )  # connect to verified address; TLS still verifies the requested hostname
            conn = (
                ssl.create_default_context().wrap_socket(raw, server_hostname=host)
                if u.scheme == "https"
                else raw
            )
            with conn:
                target = urlunsplit(("", "", u.path or "/", u.query, ""))
                target = quote(target, safe="/?&=:+,;@!$()*%~-'")
                authority = f"[{host}]" if ":" in host else host
                conn.sendall(
                    f"GET {target} HTTP/1.1\r\nHost: {authority}\r\nAccept: text/html\r\nAccept-Encoding: identity\r\nConnection: close\r\n\r\n".encode(
                        "ascii"
                    )
                )
                with http.client.HTTPResponse(conn) as r:
                    r.begin()
                    if r.status in (301, 302, 303, 307, 308):
                        if not r.getheader("Location"):
                            raise ValueError("Redirect thiếu đích")
                        url = urljoin(url, r.getheader("Location"))
                        continue
                    if r.status != 200 or r.headers.get_content_type() not in (
                        "text/html",
                        "application/xhtml+xml",
                    ):
                        raise ValueError("Expected HTML")
                    if (
                        r.getheader("Content-Encoding", "identity").lower()
                        != "identity"
                    ):
                        raise ValueError("Unsupported content encoding")
                    if "attachment" in r.getheader("Content-Disposition", "").lower():
                        raise ValueError("Expected inline HTML")
                    size = r.getheader("Content-Length")
                    if size is not None and (
                        not re.fullmatch(r"[0-9]{1,12}", size) or int(size) > limit
                    ):
                        raise ValueError("Snapshot quá lớn")
                    data = r.read(limit + 1)
                    if len(data) > limit:
                        raise ValueError("Snapshot quá lớn")
                    return url, data.decode(
                        r.headers.get_content_charset() or "utf-8", errors="replace"
                    )
    raise ValueError("Too many redirects")


def _worker(pipe, url, limit):
    try:
        pipe.send((True, fetch_inner(url, limit)))
    except FetchPolicyError:
        pipe.send((False, "policy"))
    except (ValueError, OSError, http.client.HTTPException, LookupError):
        pipe.send((False, "site"))
    except Exception:
        pipe.send((False, "worker"))
    finally:
        pipe.close()


def fetch(url, limit):
    # Bound DNS, TLS, headers and slow response bodies together.
    from multiprocessing import get_context

    ctx = get_context("spawn")
    reader, writer = ctx.Pipe(duplex=False)
    worker = ctx.Process(target=_worker, args=(writer, url, limit), daemon=True)
    worker.start()
    writer.close()
    try:
        if not reader.poll(12):
            raise TimeoutError("HTML fetch timed out")
        ok, value = reader.recv()
        if not ok:
            if value == "policy":
                raise FetchPolicyError("Destination blocked")
            if value == "site":
                raise ValueError("Document unavailable")
            raise RuntimeError("Collection failed internally")
        return value
    finally:
        reader.close()
        if worker.is_alive():
            worker.terminate()
        worker.join()
