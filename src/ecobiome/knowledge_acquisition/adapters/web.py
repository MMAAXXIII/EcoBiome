"""Generic public HTTP/HTTPS web-page acquisition for EcoBiome Collector."""

from __future__ import annotations

import http.client
import importlib.metadata
import re
import socket
import ssl
import urllib.parse
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from bs4 import BeautifulSoup
from bs4.element import Tag

from ecobiome.knowledge_acquisition.acquisition import (
    AcquisitionContext,
    AcquisitionError,
    AcquisitionRequest,
    AcquisitionResult,
    AdapterMatch,
    CanonicalSource,
    RepresentationDraft,
    RetrievedPayload,
)
from ecobiome.knowledge_acquisition.security import (
    NetworkPolicy,
    RedirectPolicyError,
    ResponsePolicyError,
    ValidatedTarget,
    sanitized_redirect_headers,
    validate_peer_ip,
    validate_redirect_chain,
    validate_response_metadata,
    validate_url,
)
from ecobiome.knowledge_acquisition.source import SourceType

_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
_TRACKING_QUERY_KEYS = frozenset(
    {
        "fbclid",
        "gclid",
        "gbraid",
        "msclkid",
        "srsltid",
        "wbraid",
    }
)
_TRACKING_QUERY_PREFIXES = ("utm_",)
_CHARSET_RE = re.compile(r"charset\s*=\s*[\"']?([^;\s\"']+)", re.IGNORECASE)


class WebAcquisitionError(AcquisitionError):
    """A public web page could not be acquired safely."""


@dataclass(frozen=True, slots=True)
class HttpResponseSnapshot:
    """Bounded response snapshot returned by the SSRF-safe transport."""

    status_code: int
    headers: dict[str, str]
    body: bytes
    peer_ip: str


@dataclass(frozen=True, slots=True)
class WebFetchSnapshot:
    """Final bounded response plus redirect metadata."""

    final_url: str
    status_code: int
    headers: dict[str, str]
    body: bytes
    redirect_urls: tuple[str, ...]
    peer_ip: str


Resolver = Callable[[str, int], Sequence[str]]
RequestOnce = Callable[
    [ValidatedTarget, Mapping[str, str], NetworkPolicy],
    HttpResponseSnapshot,
]


class WebFetcher(Protocol):
    """Fetch one public web URL without writing outside adapter staging."""

    def fetch(self, url: str, *, maximum_input_bytes: int) -> WebFetchSnapshot:
        """Fetch one bounded page."""
        ...


def _system_resolver(host: str, port: int) -> tuple[str, ...]:
    """Resolve host/port for policy validation."""
    answers = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    return tuple(sorted({str(item[4][0]) for item in answers}))


def _origin_form(target: ValidatedTarget) -> str:
    """Return RFC origin-form request target without fragments."""
    parts = urllib.parse.urlsplit(target.normalized_url)
    path = parts.path or "/"
    if parts.query:
        return f"{path}?{parts.query}"
    return path


def _connect_prevalidated_socket(
    target: ValidatedTarget,
    *,
    policy: NetworkPolicy,
) -> socket.socket:
    """Connect only to an IP that passed URL policy, preserving TLS SNI."""
    errors: list[str] = []
    for ip in target.resolved_ips:
        raw: socket.socket | None = None
        try:
            raw = socket.create_connection(
                (ip, target.port),
                timeout=policy.connect_timeout_seconds,
            )
            validate_peer_ip(target, str(raw.getpeername()[0]))
            raw.settimeout(policy.read_timeout_seconds)
            if target.scheme == "https":
                context = ssl.create_default_context()
                wrapped = context.wrap_socket(raw, server_hostname=target.host)
                wrapped.settimeout(policy.read_timeout_seconds)
                validate_peer_ip(target, str(wrapped.getpeername()[0]))
                return wrapped
            return raw
        except (OSError, ssl.SSLError, ValueError) as exc:
            if raw is not None:
                raw.close()
            errors.append(f"{ip}: {type(exc).__name__}: {exc}")

    detail = "; ".join(errors) or "no validated address"
    raise WebAcquisitionError(f"Could not connect to validated target: {detail}")


def _parse_content_length(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ResponsePolicyError("Invalid Content-Length header.") from exc
    return parsed


def _default_request_once(
    target: ValidatedTarget,
    headers: Mapping[str, str],
    policy: NetworkPolicy,
) -> HttpResponseSnapshot:
    """Perform one GET against a prevalidated DNS answer without auto-redirect."""
    sock = _connect_prevalidated_socket(target, policy=policy)
    connection: http.client.HTTPConnection
    if target.scheme == "https":
        connection = http.client.HTTPSConnection(
            target.host,
            target.port,
            timeout=policy.read_timeout_seconds,
        )
    else:
        connection = http.client.HTTPConnection(
            target.host,
            target.port,
            timeout=policy.read_timeout_seconds,
        )
    connection.sock = sock

    try:
        connection.request(
            "GET",
            _origin_form(target),
            headers=dict(headers),
        )
        response = connection.getresponse()
        peer_ip = str(sock.getpeername()[0])
        validate_peer_ip(target, peer_ip)

        response_headers = {name.lower(): value for name, value in response.getheaders()}
        content_length = _parse_content_length(response_headers.get("content-length"))

        if 200 <= response.status < 300:
            content_encoding = response_headers.get("content-encoding", "").strip().lower()
            if content_encoding not in {"", "identity"}:
                raise ResponsePolicyError(
                    "Content-Encoding is not supported by WebPageAdapter V1: "
                    f"{content_encoding}"
                )
            validate_response_metadata(
                content_type=response_headers.get("content-type"),
                content_length=content_length,
                policy=policy,
            )

        body = bytearray()
        if 200 <= response.status < 300:
            while True:
                remaining = policy.max_wire_bytes - len(body)
                if remaining < 0:
                    raise ResponsePolicyError("Wire-byte limit exceeded.")
                chunk = response.read(min(64 * 1024, remaining + 1))
                if not chunk:
                    break
                body.extend(chunk)
                if len(body) > policy.max_wire_bytes:
                    raise ResponsePolicyError("Wire-byte limit exceeded.")

        return HttpResponseSnapshot(
            status_code=response.status,
            headers=response_headers,
            body=bytes(body),
            peer_ip=peer_ip,
        )
    finally:
        connection.close()


class SafeHttpFetcher:
    """Minimal SSRF-safe HTTP transport for public text web pages."""

    def __init__(
        self,
        *,
        resolver: Resolver | None = None,
        request_once: RequestOnce | None = None,
    ) -> None:
        self._resolver = resolver or _system_resolver
        self._request_once = request_once or _default_request_once

    def fetch(self, url: str, *, maximum_input_bytes: int) -> WebFetchSnapshot:
        """Fetch one page with DNS/IP, redirect, media and byte limits."""
        if maximum_input_bytes <= 0:
            raise ValueError("maximum_input_bytes must be greater than zero")

        policy = NetworkPolicy(
            max_wire_bytes=maximum_input_bytes,
            max_decoded_bytes=maximum_input_bytes,
            allowed_content_types=("text/html", "text/plain"),
        )
        current = validate_url(url, resolver=self._resolver, policy=policy)
        headers: dict[str, str] = {
            "Accept": "text/html,text/plain;q=0.9",
            "Accept-Encoding": "identity",
            "Connection": "close",
            "User-Agent": policy.user_agent,
        }
        redirects: list[str] = []

        for _ in range(policy.max_redirects + 1):
            response = self._request_once(current, headers, policy)
            validate_peer_ip(current, response.peer_ip)

            if response.status_code in _REDIRECT_STATUSES:
                location = response.headers.get("location")
                if not location:
                    raise RedirectPolicyError(
                        "Redirect response is missing a Location header."
                    )
                next_target, hops = validate_redirect_chain(
                    current.normalized_url,
                    (location,),
                    resolver=self._resolver,
                    policy=policy,
                )
                headers = sanitized_redirect_headers(
                    headers,
                    hops[0].source,
                    next_target,
                )
                redirects.append(next_target.normalized_url)
                if len(redirects) > policy.max_redirects:
                    raise RedirectPolicyError(
                        f"Redirect count exceeds limit {policy.max_redirects}."
                    )
                current = next_target
                continue

            if not 200 <= response.status_code < 300:
                raise WebAcquisitionError(
                    f"HTTP status {response.status_code} for {current.normalized_url}"
                )

            content_type = response.headers.get("content-type")
            content_length = _parse_content_length(response.headers.get("content-length"))
            validate_response_metadata(
                content_type=content_type,
                content_length=content_length,
                policy=policy,
            )
            if len(response.body) > policy.max_wire_bytes:
                raise ResponsePolicyError("Wire-byte limit exceeded.")

            return WebFetchSnapshot(
                final_url=current.normalized_url,
                status_code=response.status_code,
                headers=dict(response.headers),
                body=response.body,
                redirect_urls=tuple(redirects),
                peer_ip=response.peer_ip,
            )

        raise RedirectPolicyError(
            f"Redirect count exceeds limit {policy.max_redirects}."
        )


def _is_tracking_key(key: str) -> bool:
    lowered = key.lower()
    return lowered in _TRACKING_QUERY_KEYS or lowered.startswith(_TRACKING_QUERY_PREFIXES)


def canonical_web_url(raw_url: str) -> str:
    """Normalize a public-web logical locator without performing DNS."""
    candidate = raw_url.strip()
    if not candidate:
        raise ValueError("Web URL is empty.")

    try:
        parts = urllib.parse.urlsplit(candidate)
    except ValueError as exc:
        raise ValueError("Web URL could not be parsed.") from exc

    scheme = parts.scheme.lower()
    if scheme not in {"http", "https"}:
        raise ValueError("WebPageAdapter accepts HTTP/HTTPS URLs only.")
    if parts.username is not None or parts.password is not None:
        raise ValueError("Embedded URL credentials are forbidden.")
    if not parts.hostname:
        raise ValueError("Web URL does not contain a host.")

    host = parts.hostname.strip().rstrip(".")
    if not host:
        raise ValueError("Web URL host is empty.")
    try:
        host = host.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ValueError("Web URL host cannot be IDNA-normalized.") from exc

    try:
        port = parts.port
    except ValueError as exc:
        raise ValueError("Web URL port is invalid.") from exc

    authority = f"[{host}]" if ":" in host else host
    default_port = 80 if scheme == "http" else 443
    if port is not None and port != default_port:
        authority = f"{authority}:{port}"

    query_items = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
    filtered_query = urllib.parse.urlencode(
        [(key, value) for key, value in query_items if not _is_tracking_key(key)],
        doseq=True,
    )
    return urllib.parse.urlunsplit(
        (scheme, authority, parts.path or "/", filtered_query, "")
    )


def _charset_from_content_type(content_type: str) -> str | None:
    match = _CHARSET_RE.search(content_type)
    if match is None:
        return None
    return match.group(1).strip()


def _html_to_text(raw: bytes, content_type: str) -> tuple[str, dict[str, str]]:
    """Derive visible reading text and basic page metadata from HTML."""
    hinted_charset = _charset_from_content_type(content_type)
    soup = BeautifulSoup(raw, "html.parser", from_encoding=hinted_charset)

    title = ""
    if isinstance(soup.title, Tag):
        title = soup.title.get_text(" ", strip=True)
    if not title:
        og_title = soup.find("meta", attrs={"property": "og:title"})
        if isinstance(og_title, Tag):
            title = str(og_title.get("content") or "").strip()

    author = ""
    author_meta = soup.find("meta", attrs={"name": re.compile(r"^author$", re.IGNORECASE)})
    if isinstance(author_meta, Tag):
        author = str(author_meta.get("content") or "").strip()

    language = ""
    if isinstance(soup.html, Tag):
        language = str(soup.html.get("lang") or "").strip().lower()

    for tag in soup(["script", "style", "noscript", "template", "svg"]):
        tag.decompose()

    main = soup.find("main")
    article = soup.find("article")
    if isinstance(main, Tag):
        root: Tag | BeautifulSoup = main
    elif isinstance(article, Tag):
        root = article
    elif isinstance(soup.body, Tag):
        root = soup.body
    else:
        root = soup
    lines = [value.strip() for value in root.stripped_strings if value.strip()]
    text = "\n".join(lines)
    metadata = {
        "title": title,
        "author": author,
        "language": language,
        "detected_encoding": str(soup.original_encoding or hinted_charset or ""),
    }
    return text, metadata


def _plain_text(raw: bytes, content_type: str) -> tuple[str, dict[str, str]]:
    charset = _charset_from_content_type(content_type) or "utf-8"
    try:
        text = raw.decode(charset)
    except (LookupError, UnicodeDecodeError) as exc:
        raise WebAcquisitionError(
            f"Could not decode text/plain response using charset {charset!r}."
        ) from exc
    return text, {"title": "", "author": "", "language": "", "detected_encoding": charset}


class WebPageAdapter:
    """Acquire arbitrary public HTML/text pages through the Collector URL guard."""

    name = "web-page"
    version = "1"
    priority = 50

    def __init__(self, *, fetcher: WebFetcher | None = None) -> None:
        self._fetcher = fetcher or SafeHttpFetcher()

    def match(self, request: AcquisitionRequest) -> AdapterMatch | None:
        """Match generic HTTP/HTTPS URLs below specialized adapter priority."""
        try:
            parts = urllib.parse.urlsplit(request.locator.strip())
        except ValueError:
            return None
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
            return None
        return AdapterMatch(
            priority=self.priority,
            reason="generic_public_http_or_https_url",
        )

    def canonicalize(self, request: AcquisitionRequest) -> CanonicalSource:
        """Canonicalize syntax and tracking parameters without network access."""
        canonical = canonical_web_url(request.locator)
        parts = urllib.parse.urlsplit(canonical)
        title = Path(parts.path).name or parts.hostname or canonical
        return CanonicalSource(
            source_type=SourceType.OTHER.value,
            canonical_locator=canonical,
            title=title,
            language=request.language,
            metadata={"adapter": self.name, "host": parts.hostname or ""},
        )

    @staticmethod
    def _stage_bytes(
        *,
        context: AcquisitionContext,
        prefix: str,
        suffix: str,
        raw: bytes,
    ) -> Path:
        if len(raw) > context.maximum_input_bytes:
            raise ValueError(
                "Web staged payload exceeds maximum_input_bytes: "
                f"{len(raw)} > {context.maximum_input_bytes}"
            )
        context.staging_directory.mkdir(parents=True, exist_ok=True)
        path = context.staging_directory / f"{prefix}-{uuid4().hex}{suffix}"
        path.write_bytes(raw)
        return path

    def acquire(
        self,
        request: AcquisitionRequest,
        context: AcquisitionContext,
    ) -> AcquisitionResult:
        """Fetch exact bytes then derive a normalized visible-text representation."""
        canonical = self.canonicalize(request)
        snapshot = self._fetcher.fetch(
            request.locator,
            maximum_input_bytes=context.maximum_input_bytes,
        )
        content_type = snapshot.headers.get("content-type", "")
        base_type = content_type.split(";", 1)[0].strip().lower()

        if base_type == "text/html":
            text, page = _html_to_text(snapshot.body, content_type)
            derivation_method = "beautifulsoup_visible_text_v1"
            tool_name = "beautifulsoup4"
            try:
                tool_version = importlib.metadata.version("beautifulsoup4")
            except importlib.metadata.PackageNotFoundError:
                tool_version = "unknown"
        elif base_type == "text/plain":
            text, page = _plain_text(snapshot.body, content_type)
            derivation_method = "decode_declared_charset"
            tool_name = self.name
            tool_version = self.version
        else:
            raise WebAcquisitionError(
                f"WebPageAdapter cannot derive text from Content-Type {base_type!r}."
            )

        if not text.strip():
            raise WebAcquisitionError("Web page produced no visible text.")

        normalized_raw = text.encode("utf-8")
        if len(normalized_raw) > context.maximum_input_bytes:
            raise ValueError(
                "Derived web text exceeds maximum_input_bytes: "
                f"{len(normalized_raw)} > {context.maximum_input_bytes}"
            )

        raw_path = self._stage_bytes(
            context=context,
            prefix="web-raw",
            suffix=".bin",
            raw=snapshot.body,
        )
        text_path = self._stage_bytes(
            context=context,
            prefix="web-text",
            suffix=".utf8",
            raw=normalized_raw,
        )

        title = page["title"] or canonical.title
        author = page["author"]
        language = page["language"] or request.language
        source = CanonicalSource(
            source_type=canonical.source_type,
            canonical_locator=canonical.canonical_locator,
            title=title,
            author=author,
            language=language,
            metadata={
                **canonical.metadata,
                "final_url": snapshot.final_url,
                "redirect_urls": list(snapshot.redirect_urls),
                "http_status": snapshot.status_code,
                "content_type": content_type,
            },
        )

        payload = RetrievedPayload(
            logical_key="web-raw",
            staged_path=raw_path,
            media_type=base_type,
            original_locator=request.locator,
            canonical_locator=canonical.canonical_locator,
            protocol=urllib.parse.urlsplit(snapshot.final_url).scheme,
            request_metadata={
                "adapter": self.name,
                "maximum_input_bytes": context.maximum_input_bytes,
            },
            response_metadata={
                "http_status": snapshot.status_code,
                "content_type": content_type,
                "final_url": snapshot.final_url,
                "redirect_urls": list(snapshot.redirect_urls),
                "peer_ip": snapshot.peer_ip,
                "size_bytes": len(snapshot.body),
            },
        )
        representation = RepresentationDraft(
            logical_key="web-visible-text",
            staged_path=text_path,
            representation_kind="normalized_text",
            media_type="text/plain; charset=utf-8",
            language=language,
            parent_payload_key="web-raw",
            derivation_method=derivation_method,
            tool_name=tool_name,
            tool_version=tool_version,
            derivation_parameters={
                "profile": "web-page-v1",
                "boilerplate_strategy": "main_or_article_or_body",
                "scripts_styles_removed": True,
            },
            metadata={
                "source_media_type": base_type,
                "source_title": title,
                "source_author": author,
                "detected_encoding": page["detected_encoding"],
            },
            text=text,
        )

        return AcquisitionResult(
            canonical_source=source,
            payloads=(payload,),
            representations=(representation,),
        )
