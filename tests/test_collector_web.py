"""No-network tests for the generic Collector public web-page adapter."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest

from ecobiome.knowledge_acquisition.acquisition import (
    AcquisitionContext,
    AcquisitionRequest,
)
from ecobiome.knowledge_acquisition.adapters.web import (
    HttpResponseSnapshot,
    SafeHttpFetcher,
    WebFetchSnapshot,
    WebPageAdapter,
    canonical_web_url,
)
from ecobiome.knowledge_acquisition.collector_acquire import default_adapter_registry
from ecobiome.knowledge_acquisition.security import (
    BlockedAddressError,
    NetworkPolicy,
    ValidatedTarget,
)


class FixtureFetcher:
    """Deterministic web snapshot fixture; never performs network I/O."""

    def __init__(self, snapshot: WebFetchSnapshot) -> None:
        self.snapshot = snapshot
        self.calls: list[tuple[str, int]] = []

    def fetch(self, url: str, *, maximum_input_bytes: int) -> WebFetchSnapshot:
        self.calls.append((url, maximum_input_bytes))
        return self.snapshot


def _html_snapshot() -> WebFetchSnapshot:
    html = b"""<!doctype html>
<html lang="fr">
<head>
  <title>Les algues en aquarium</title>
  <meta name="author" content="Eco Auteur">
  <style>.hidden { display:none }</style>
  <script>window.secret = 'ignore';</script>
</head>
<body>
  <nav>Navigation bruit</nav>
  <main>
    <h1>Comprendre les algues</h1>
    <p>La lumiere et les nutriments influencent leur developpement.</p>
  </main>
</body>
</html>"""
    return WebFetchSnapshot(
        final_url="https://www.fishfish.fr/algue",
        status_code=200,
        headers={
            "content-type": "text/html; charset=utf-8",
            "content-length": str(len(html)),
        },
        body=html,
        redirect_urls=(),
        peer_ip="93.184.216.34",
    )


def test_generic_web_adapter_matches_public_http_urls() -> None:
    adapter = WebPageAdapter(fetcher=FixtureFetcher(_html_snapshot()))

    fishfish = adapter.match(AcquisitionRequest("https://www.fishfish.fr/algue"))
    ammannia = adapter.match(
        AcquisitionRequest(
            "https://www.ammannia.com/guides-avances-les-algues-les-reconnaitre-les-combattre.html"
        )
    )

    assert fishfish is not None
    assert fishfish.reason == "generic_public_http_or_https_url"
    assert ammannia is not None


def test_generic_web_canonicalization_removes_tracking_only() -> None:
    canonical = canonical_web_url(
        "HTTPS://WWW.AMMANNIA.COM/guides.html?x=1&utm_source=google&"
        "srsltid=tracker&lang=fr#section"
    )

    assert canonical == "https://www.ammannia.com/guides.html?x=1&lang=fr"


def test_default_registry_prefers_specialized_youtube_adapter() -> None:
    registry = default_adapter_registry()

    youtube, youtube_match = registry.select(
        AcquisitionRequest("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    )
    generic, generic_match = registry.select(
        AcquisitionRequest("https://www.fishfish.fr/algue")
    )

    assert youtube.name == "youtube"
    assert youtube_match.priority > generic_match.priority
    assert generic.name == "web-page"


def test_web_adapter_stages_raw_html_and_visible_main_text(tmp_path: Path) -> None:
    fetcher = FixtureFetcher(_html_snapshot())
    adapter = WebPageAdapter(fetcher=fetcher)
    request = AcquisitionRequest(
        "https://www.fishfish.fr/algue?utm_source=test",
        language="fr",
        maximum_input_bytes=4096,
    )
    context = AcquisitionContext(
        staging_directory=tmp_path / "staging",
        maximum_input_bytes=4096,
    )

    result = adapter.acquire(request, context)

    assert fetcher.calls == [(request.locator, 4096)]
    assert result.canonical_source.canonical_locator == "https://www.fishfish.fr/algue"
    assert result.canonical_source.title == "Les algues en aquarium"
    assert result.canonical_source.author == "Eco Auteur"
    assert result.canonical_source.language == "fr"
    assert result.payloads[0].staged_path.read_bytes() == _html_snapshot().body

    representation = result.representations[0]
    assert representation.representation_kind == "normalized_text"
    assert representation.text is not None
    assert "Comprendre les algues" in representation.text
    assert "La lumiere et les nutriments" in representation.text
    assert "Navigation bruit" not in representation.text
    assert "window.secret" not in representation.text


def test_safe_fetcher_revalidates_redirect_before_second_request() -> None:
    mapping = {
        "public.example": ("93.184.216.34",),
        "private.example": ("127.0.0.1",),
    }
    calls: list[str] = []

    def resolver(host: str, port: int) -> tuple[str, ...]:
        del port
        return mapping.get(host, ())

    def request_once(
        target: ValidatedTarget,
        headers: Mapping[str, str],
        policy: NetworkPolicy,
    ) -> HttpResponseSnapshot:
        del headers, policy
        normalized_url = target.normalized_url
        calls.append(normalized_url)
        return HttpResponseSnapshot(
            status_code=302,
            headers={"location": "http://private.example/internal"},
            body=b"",
            peer_ip="93.184.216.34",
        )

    fetcher = SafeHttpFetcher(resolver=resolver, request_once=request_once)

    with pytest.raises(BlockedAddressError):
        fetcher.fetch("https://public.example/start", maximum_input_bytes=1024)

    assert calls == ["https://public.example/start"]
