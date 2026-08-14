"""No-network tests for Collector URL/SSRF policy."""

from __future__ import annotations

import gzip

import pytest

from ecobiome.knowledge_acquisition.security import (
    BlockedAddressError,
    InvalidUrlError,
    NetworkPolicy,
    RedirectPolicyError,
    ResponsePolicyError,
    consume_gzip_body,
    consume_identity_body,
    sanitized_redirect_headers,
    validate_peer_ip,
    validate_redirect_chain,
    validate_response_metadata,
    validate_url,
)


class FixtureResolver:
    """Deterministic resolver fixture; never performs DNS."""

    def __init__(self) -> None:
        self.mapping = {
            "public.example": ("93.184.216.34",),
            "public2.example": ("1.1.1.1",),
            "private.example": ("192.168.1.20",),
            "loopback.example": ("127.0.0.1",),
            "loopback6.example": ("::1",),
            "linklocal.example": ("169.254.169.254",),
            "private6.example": ("fd00::1234",),
            "mixed.example": ("93.184.216.34", "10.0.0.4"),
            "mapped.example": ("::ffff:127.0.0.1",),
        }

    def __call__(self, host: str, port: int) -> tuple[str, ...]:
        del port
        return self.mapping.get(host, ())


@pytest.fixture
def resolver() -> FixtureResolver:
    return FixtureResolver()


@pytest.fixture
def policy() -> NetworkPolicy:
    return NetworkPolicy(
        max_wire_bytes=256,
        max_decoded_bytes=1024,
    )


def test_public_https_is_allowed(
    resolver: FixtureResolver,
    policy: NetworkPolicy,
) -> None:
    target = validate_url(
        "https://public.example/science?q=pond#fragment",
        resolver=resolver,
        policy=policy,
    )
    assert target.normalized_url == (
        "https://public.example/science?q=pond"
    )
    assert target.resolved_ips == ("93.184.216.34",)


@pytest.mark.parametrize(
    "url",
    [
        "ftp://public.example/file",
        "file:///etc/passwd",
        "javascript:alert(1)",
    ],
)
def test_disallowed_schemes_are_blocked(
    url: str,
    resolver: FixtureResolver,
    policy: NetworkPolicy,
) -> None:
    with pytest.raises(InvalidUrlError):
        validate_url(url, resolver=resolver, policy=policy)


def test_embedded_credentials_are_blocked(
    resolver: FixtureResolver,
    policy: NetworkPolicy,
) -> None:
    with pytest.raises(InvalidUrlError, match="credentials"):
        validate_url(
            "https://user:secret@public.example/",
            resolver=resolver,
            policy=policy,
        )


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/",
        "http://printer.local/",
        "http://127.0.0.1/",
        "http://10.0.0.1/",
        "http://private.example/",
        "http://loopback.example/",
        "http://loopback6.example/",
        "http://linklocal.example/latest/meta-data/",
        "http://private6.example/",
        "http://mapped.example/",
        "https://mixed.example/",
    ],
)
def test_local_private_and_mixed_targets_are_blocked(
    url: str,
    resolver: FixtureResolver,
    policy: NetworkPolicy,
) -> None:
    with pytest.raises(BlockedAddressError):
        validate_url(url, resolver=resolver, policy=policy)


def test_redirect_target_is_revalidated(
    resolver: FixtureResolver,
    policy: NetworkPolicy,
) -> None:
    with pytest.raises(BlockedAddressError):
        validate_redirect_chain(
            "https://public.example/start",
            ("http://private.example/internal",),
            resolver=resolver,
            policy=policy,
        )


def test_https_downgrade_is_blocked(
    resolver: FixtureResolver,
    policy: NetworkPolicy,
) -> None:
    with pytest.raises(RedirectPolicyError, match="downgrade"):
        validate_redirect_chain(
            "https://public.example/start",
            ("http://public2.example/end",),
            resolver=resolver,
            policy=policy,
        )


def test_redirect_limit_is_enforced(
    resolver: FixtureResolver,
    policy: NetworkPolicy,
) -> None:
    locations = tuple(
        f"https://public.example/{index}"
        for index in range(policy.max_redirects + 1)
    )
    with pytest.raises(RedirectPolicyError, match="limit"):
        validate_redirect_chain(
            "https://public.example/start",
            locations,
            resolver=resolver,
            policy=policy,
        )


def test_cross_origin_sensitive_headers_are_removed(
    resolver: FixtureResolver,
    policy: NetworkPolicy,
) -> None:
    final, hops = validate_redirect_chain(
        "https://public.example/start",
        ("https://public2.example/end",),
        resolver=resolver,
        policy=policy,
    )
    headers = sanitized_redirect_headers(
        {
            "Authorization": "Bearer secret",
            "Cookie": "session=secret",
            "Accept": "text/html",
        },
        hops[0].source,
        final,
    )
    assert headers == {"Accept": "text/html"}


def test_peer_ip_must_match_prevalidated_answer(
    resolver: FixtureResolver,
    policy: NetworkPolicy,
) -> None:
    target = validate_url(
        "https://public.example/",
        resolver=resolver,
        policy=policy,
    )
    validate_peer_ip(target, "93.184.216.34")

    with pytest.raises(BlockedAddressError, match="prevalidated"):
        validate_peer_ip(target, "1.1.1.1")


def test_response_metadata_limits(
    policy: NetworkPolicy,
) -> None:
    validate_response_metadata(
        content_type="text/html; charset=utf-8",
        content_length=100,
        policy=policy,
    )

    with pytest.raises(ResponsePolicyError, match="Content-Type"):
        validate_response_metadata(
            content_type="application/x-msdownload",
            content_length=100,
            policy=policy,
        )

    with pytest.raises(ResponsePolicyError, match="wire-byte"):
        validate_response_metadata(
            content_type="text/plain",
            content_length=policy.max_wire_bytes + 1,
            policy=policy,
        )


def test_streamed_wire_limit(
    policy: NetworkPolicy,
) -> None:
    with pytest.raises(ResponsePolicyError, match="Wire-byte"):
        consume_identity_body(
            (b"a" * 200, b"b" * 100),
            policy=policy,
        )


def test_decoded_decompression_limit(
    policy: NetworkPolicy,
) -> None:
    compressed = gzip.compress(
        b"X" * (policy.max_decoded_bytes + 100)
    )
    assert len(compressed) < policy.max_wire_bytes

    with pytest.raises(ResponsePolicyError, match="Decoded-byte"):
        consume_gzip_body(
            (compressed,),
            policy=policy,
        )
