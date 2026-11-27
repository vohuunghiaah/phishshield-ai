from phishshield.features.url_features import url_features
from phishshield.features.html_features import html_features

VERSION = "1.0.0"


def extract_features(url: str, html: str | None):
    row = url_features(url)
    if html is not None:
        row.update(html_features(url, html))
    return row


def schema(modality):
    if modality not in {"url_only", "url_html"}:
        raise ValueError(modality)
    return list(
        extract_features(
            "https://example.org/", "<html/>" if modality == "url_html" else None
        )
    )
