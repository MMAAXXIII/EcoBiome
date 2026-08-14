"""No-network URL and response policy for Collector HTTP adapters."""

from __future__ import annotations

import ipaddress
import urllib.parse
import zlib
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass

Resolver = Callable[[str, int], Sequence[str]]


class SecurityPolicyError(ValueError):
    """Base error for Collector acquisition security policy failures."""


class InvalidUrlError(SecurityPolicyError):
    """URL syntax or scheme violates Collector policy."""


class BlockedAddressError(SecurityPolicyError):
    """A hostname or resolved address is not safe for outbound acquisition."""


class RedirectPolicyError(SecurityPolicyError):
    """A redirect chain violates Collector acquisition policy."""


class ResponsePolicyError(SecurityPolicyError):
    """Response metadata or bytes violate Collector resource policy."""


@dataclass(frozen=True, slots=True)
class NetworkPolicy:
    """Bound the future HTTP transport before any request is sent."""

    allowed_schemes: tuple[str, ...] = ("http", "https")
    connect_timeout_seconds: float = 5.0
    read_timeout_seconds: float = 30.0
    max_redirects: int = 5
    max_url_characters: int = 4096
    max_wire_bytes: int = 8 * 1024 * 1024
    max_decoded_bytes: int = 32 * 1024 * 1024
    forbid_https_downgrade: bool = True
    user_agent: str = "EcoBiome-Collector/0.1"
    allowed_content_types: tuple[str, ...] = (
        "text/html",
        "text/plain",
        "application/json",
        "application/pdf",
    )


@dataclass(frozen=True, slots=True)
class ValidatedTarget:
    """One URL target whose DNS answer set has passed policy."""

    original_url: str
    normalized_url: str
    scheme: str
    host: str
    port: int
    resolved_ips: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RedirectHop:
    """One validated redirect transition."""

    source: ValidatedTarget
    location: str
    target: ValidatedTarget


@dataclass(frozen=True, slots=True)
class BodyUsage:
    """Count transport and decoded response bytes."""

    wire_bytes: int
    decoded_bytes: int


SENSITIVE_REDIRECT_HEADERS = frozenset(
    {"authorization", "cookie", "proxy-authorization"}
)
LOCAL_HOSTNAME_DENYLIST = frozenset(
    {
        "localhost",
        "localhost.localdomain",
        "ip6-localhost",
        "ip6-loopback",
    }
)


def _normalize_host(host: str) -> str:
    stripped = host.strip().rstrip(".")
    if not stripped:
        raise InvalidUrlError("URL host is empty.")
    if any(ord(character) < 32 for character in stripped):
        raise InvalidUrlError("URL host contains a control character.")
    try:
        return stripped.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise InvalidUrlError(
            "URL host cannot be IDNA-normalized."
        ) from exc


def _default_port(scheme: str) -> int:
    if scheme == "http":
        return 80
    if scheme == "https":
        return 443
    raise InvalidUrlError(f"Unsupported URL scheme: {scheme}")


def _normalize_ip(
    value: str,
) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    try:
        address = ipaddress.ip_address(value)
    except ValueError as exc:
        raise BlockedAddressError(
            f"Resolver returned invalid IP address: {value}"
        ) from exc

    if isinstance(address, ipaddress.IPv6Address):
        mapped = address.ipv4_mapped
        if mapped is not None:
            return mapped
    return address


def _ensure_public_address(
    address: ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> None:
    if address.is_loopback:
        raise BlockedAddressError(f"Loopback address blocked: {address}")
    if address.is_private:
        raise BlockedAddressError(f"Private address blocked: {address}")
    if address.is_link_local:
        raise BlockedAddressError(f"Link-local address blocked: {address}")
    if address.is_multicast:
        raise BlockedAddressError(f"Multicast address blocked: {address}")
    if address.is_reserved:
        raise BlockedAddressError(f"Reserved address blocked: {address}")
    if address.is_unspecified:
        raise BlockedAddressError(f"Unspecified address blocked: {address}")
    if not address.is_global:
        raise BlockedAddressError(f"Non-global address blocked: {address}")


def validate_url(
    raw_url: str,
    *,
    resolver: Resolver,
    policy: NetworkPolicy | None = None,
) -> ValidatedTarget:
    """Validate syntax and every resolved address without making a request."""
    active_policy = policy or NetworkPolicy()
    candidate = raw_url.strip()

    if not candidate:
        raise InvalidUrlError("URL is empty.")
    if len(candidate) > active_policy.max_url_characters:
        raise InvalidUrlError("URL exceeds maximum configured length.")
    if any(ord(character) < 32 for character in candidate):
        raise InvalidUrlError("URL contains a control character.")

    try:
        parts = urllib.parse.urlsplit(candidate)
    except ValueError as exc:
        raise InvalidUrlError("URL could not be parsed.") from exc

    scheme = parts.scheme.lower()
    if scheme not in active_policy.allowed_schemes:
        raise InvalidUrlError(
            f"URL scheme is not allowed: {scheme or '<none>'}"
        )

    if parts.username is not None or parts.password is not None:
        raise InvalidUrlError("Embedded URL credentials are forbidden.")
    if not parts.hostname:
        raise InvalidUrlError("URL does not contain a host.")

    host = _normalize_host(parts.hostname)
    if (
        host in LOCAL_HOSTNAME_DENYLIST
        or host.endswith((".localhost", ".local"))
    ):
        raise BlockedAddressError(f"Local hostname blocked: {host}")

    try:
        port = parts.port or _default_port(scheme)
    except ValueError as exc:
        raise InvalidUrlError("URL port is invalid.") from exc

    if not 1 <= port <= 65535:
        raise InvalidUrlError("URL port is outside 1..65535.")

    resolved: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
    try:
        literal = _normalize_ip(host)
    except BlockedAddressError:
        literal = None

    if literal is not None:
        _ensure_public_address(literal)
        resolved.append(literal)
    else:
        answers = tuple(resolver(host, port))
        if not answers:
            raise BlockedAddressError(
                f"DNS resolution returned no addresses for {host}."
            )
        for value in answers:
            address = _normalize_ip(str(value))
            _ensure_public_address(address)
            resolved.append(address)

    unique_ips = tuple(sorted({str(address) for address in resolved}))
    normalized_host = f"[{host}]" if ":" in host else host
    authority = normalized_host
    default_port = _default_port(scheme)
    if port != default_port:
        authority = f"{authority}:{port}"

    normalized_url = urllib.parse.urlunsplit(
        (
            scheme,
            authority,
            parts.path or "/",
            parts.query,
            "",
        )
    )
    return ValidatedTarget(
        original_url=candidate,
        normalized_url=normalized_url,
        scheme=scheme,
        host=host,
        port=port,
        resolved_ips=unique_ips,
    )


def validate_redirect_chain(
    initial_url: str,
    locations: Sequence[str],
    *,
    resolver: Resolver,
    policy: NetworkPolicy | None = None,
) -> tuple[ValidatedTarget, tuple[RedirectHop, ...]]:
    """Validate every redirect target before a future transport follows it."""
    active_policy = policy or NetworkPolicy()
    if len(locations) > active_policy.max_redirects:
        raise RedirectPolicyError(
            f"Redirect count exceeds limit {active_policy.max_redirects}."
        )

    current = validate_url(
        initial_url,
        resolver=resolver,
        policy=active_policy,
    )
    hops: list[RedirectHop] = []

    for location in locations:
        target_url = urllib.parse.urljoin(
            current.normalized_url,
            location,
        )
        target = validate_url(
            target_url,
            resolver=resolver,
            policy=active_policy,
        )
        if (
            active_policy.forbid_https_downgrade
            and current.scheme == "https"
            and target.scheme == "http"
        ):
            raise RedirectPolicyError(
                "HTTPS to HTTP redirect downgrade is forbidden."
            )

        hops.append(
            RedirectHop(
                source=current,
                location=location,
                target=target,
            )
        )
        current = target

    return current, tuple(hops)


def validate_peer_ip(target: ValidatedTarget, peer_ip: str) -> None:
    """Require the connected peer to match the validated DNS answer set."""
    address = _normalize_ip(peer_ip)
    _ensure_public_address(address)
    normalized = str(address)

    if normalized not in target.resolved_ips:
        raise BlockedAddressError(
            "Connected peer IP was not in the prevalidated DNS answer set: "
            f"{normalized}"
        )


def sanitized_redirect_headers(
    headers: Mapping[str, str],
    source: ValidatedTarget,
    target: ValidatedTarget,
) -> dict[str, str]:
    """Drop sensitive headers when a redirect changes origin."""
    source_origin = (source.scheme, source.host, source.port)
    target_origin = (target.scheme, target.host, target.port)
    cross_origin = source_origin != target_origin

    output: dict[str, str] = {}
    for name, value in headers.items():
        if cross_origin and name.lower() in SENSITIVE_REDIRECT_HEADERS:
            continue
        output[name] = value
    return output


def validate_response_metadata(
    *,
    content_type: str | None,
    content_length: int | None,
    policy: NetworkPolicy | None = None,
) -> None:
    """Validate response media type and declared wire size."""
    active_policy = policy or NetworkPolicy()
    if content_type is None:
        raise ResponsePolicyError("Missing Content-Type.")

    base_type = content_type.split(";", 1)[0].strip().lower()
    allowed = {item.lower() for item in active_policy.allowed_content_types}
    if base_type not in allowed:
        raise ResponsePolicyError(
            f"Content-Type is not allowed: {base_type}"
        )

    if content_length is not None:
        if content_length < 0:
            raise ResponsePolicyError("Negative Content-Length.")
        if content_length > active_policy.max_wire_bytes:
            raise ResponsePolicyError(
                "Declared Content-Length exceeds wire-byte limit."
            )


class BodyMeter:
    """Track response wire and decoded byte limits."""

    def __init__(self, policy: NetworkPolicy | None = None) -> None:
        self._policy = policy or NetworkPolicy()
        self._wire_bytes = 0
        self._decoded_bytes = 0

    def add_wire(self, amount: int) -> None:
        if amount < 0:
            raise ResponsePolicyError("Negative wire byte count.")
        self._wire_bytes += amount
        if self._wire_bytes > self._policy.max_wire_bytes:
            raise ResponsePolicyError("Wire-byte limit exceeded.")

    def add_decoded(self, amount: int) -> None:
        if amount < 0:
            raise ResponsePolicyError("Negative decoded byte count.")
        self._decoded_bytes += amount
        if self._decoded_bytes > self._policy.max_decoded_bytes:
            raise ResponsePolicyError("Decoded-byte limit exceeded.")

    def snapshot(self) -> BodyUsage:
        return BodyUsage(
            wire_bytes=self._wire_bytes,
            decoded_bytes=self._decoded_bytes,
        )


def consume_identity_body(
    chunks: Iterable[bytes],
    *,
    policy: NetworkPolicy | None = None,
) -> BodyUsage:
    """Exercise resource limits for an uncompressed streamed response."""
    meter = BodyMeter(policy)
    for chunk in chunks:
        meter.add_wire(len(chunk))
        meter.add_decoded(len(chunk))
    return meter.snapshot()


def consume_gzip_body(
    chunks: Iterable[bytes],
    *,
    policy: NetworkPolicy | None = None,
) -> BodyUsage:
    """Exercise wire and decoded limits for a gzip streamed response."""
    meter = BodyMeter(policy)
    decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)

    for chunk in chunks:
        meter.add_wire(len(chunk))
        decoded = decoder.decompress(chunk)
        meter.add_decoded(len(decoded))

    tail = decoder.flush()
    meter.add_decoded(len(tail))
    return meter.snapshot()
