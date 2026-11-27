import math
import pytest
from phishshield.features.pipeline import extract_features, schema


def test_url_features():
    f = extract_features("https://a.b.example.co.uk:443/login?c=2&d=%20", None)
    assert list(f) == schema("url_only")
    assert (
        f["subdomain_count"],
        f["explicit_port"],
        f["encoded_count"],
        f["query_count"],
    ) == (2, 1, 1, 2)
    assert f["keyword_count"] == 1 and f["https"] == 1 and math.isfinite(f["entropy"])


def test_relative_private_suffix_and_base():
    url = "https://a.github.io/path/"
    html = '<base href="https://b.github.io/"><a href="x">x</a><a href="https://a.github.io/y">y</a><form action="save"><input type="password"></form><script src="/test.js"></script>'
    f = extract_features(url, html)
    assert list(f) == schema("url_html")
    assert (
        f["external_link_ratio"],
        f["external_action_count"],
        f["external_script_count"],
    ) == (0.5, 1, 1)
    assert f["sensitive_input"] and f["password_count"] == 1


@pytest.mark.parametrize(
    "url",
    ["file:///tmp/a", "http://[", "http://host.invalid:99999", "https://a b.test/"],
)
def test_bad_urls(url):
    with pytest.raises(ValueError):
        extract_features(url, None)


def test_blank_html():
    with pytest.raises(ValueError):
        extract_features("https://example.org", " ")


def test_ip_host():
    assert extract_features("http://[2001:db8::1]/", None)["ip_host"] == 1
