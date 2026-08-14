"""Local text-file acquisition adapter for EcoBiome Collector Sprint B."""

from __future__ import annotations

import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from uuid import uuid4

from ecobiome.knowledge_acquisition.acquisition import (
    AcquisitionContext,
    AcquisitionRequest,
    AcquisitionResult,
    AdapterMatch,
    CanonicalSource,
    RepresentationDraft,
    RetrievedPayload,
)
from ecobiome.knowledge_acquisition.source import SourceType

WINDOWS_DRIVE_PATH = re.compile(r"^[A-Za-z]:[\\/]")
SUPPORTED_SUFFIXES = {
    ".csv": "text/csv",
    ".htm": "text/html",
    ".html": "text/html",
    ".json": "application/json",
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".xml": "application/xml",
}


class LocalFileAdapter:
    """Acquire bounded UTF-8 text-like files without any network access."""

    name = "local-file"
    version = "1"
    priority = 100

    def match(self, request: AcquisitionRequest) -> AdapterMatch | None:
        """Match local paths/file URLs and reject all other URI schemes."""
        locator = request.locator.strip()
        if not locator:
            return None
        if locator.startswith(("\\\\", "//")):
            return None
        if WINDOWS_DRIVE_PATH.match(locator):
            return AdapterMatch(
                priority=self.priority,
                reason="windows_local_drive_path",
            )

        parts = urllib.parse.urlsplit(locator)
        if parts.scheme and parts.scheme.lower() != "file":
            return None

        return AdapterMatch(
            priority=self.priority,
            reason="local_path_or_file_url",
        )

    def _path_from_request(self, request: AcquisitionRequest) -> Path:
        locator = request.locator.strip()
        if locator.startswith(("\\\\", "//")):
            raise ValueError("UNC/network file paths are not supported.")

        if WINDOWS_DRIVE_PATH.match(locator):
            path = Path(locator)
            parts = None
        else:
            parts = urllib.parse.urlsplit(locator)

        if parts is not None and parts.scheme.lower() == "file":
            if parts.netloc not in {"", "localhost"}:
                raise ValueError(
                    "Remote file:// authorities are not supported."
                )
            raw_path = urllib.request.url2pathname(parts.path)
            if os.name == "nt" and re.match(r"^/[A-Za-z]:/", raw_path):
                raw_path = raw_path[1:]
            path = Path(raw_path)
        elif parts is not None and parts.scheme:
            raise ValueError(
                f"Unsupported local-file URI scheme: {parts.scheme}"
            )
        else:
            path = Path(locator)

        resolved = path.expanduser().resolve()
        if not resolved.is_file():
            raise FileNotFoundError(resolved)
        return resolved

    def canonicalize(self, request: AcquisitionRequest) -> CanonicalSource:
        """Canonicalize a local file to its absolute file URI."""
        path = self._path_from_request(request)
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_SUFFIXES:
            raise ValueError(
                "Unsupported local text-file extension: "
                f"{suffix or '<none>'}"
            )

        return CanonicalSource(
            source_type=SourceType.OTHER.value,
            canonical_locator=path.as_uri(),
            title=path.name,
            language=request.language,
            metadata={
                "adapter": self.name,
                "local_suffix": suffix,
            },
        )

    def acquire(
        self,
        request: AcquisitionRequest,
        context: AcquisitionContext,
    ) -> AcquisitionResult:
        """Copy exact bytes to staging and derive one UTF-8 text view."""
        if context.maximum_input_bytes <= 0:
            raise ValueError("maximum_input_bytes must be greater than zero")

        source = self.canonicalize(request)
        path = self._path_from_request(request)
        size = path.stat().st_size
        if size > context.maximum_input_bytes:
            raise ValueError(
                "Local file exceeds maximum_input_bytes: "
                f"{size} > {context.maximum_input_bytes}"
            )

        context.staging_directory.mkdir(parents=True, exist_ok=True)
        raw_path = context.staging_directory / f"raw-{uuid4().hex}.bin"

        copied = 0
        with path.open("rb") as source_stream, raw_path.open("xb") as output:
            while True:
                chunk = source_stream.read(1024 * 1024)
                if not chunk:
                    break
                copied += len(chunk)
                if copied > context.maximum_input_bytes:
                    raise ValueError(
                        "Local file exceeded maximum_input_bytes while reading."
                    )
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())

        raw = raw_path.read_bytes()
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError(
                "LocalFileAdapter v1 accepts UTF-8 text files only."
            ) from exc

        if "\x00" in text:
            raise ValueError(
                "LocalFileAdapter rejected a NUL-containing binary-like file."
            )

        normalized_path = (
            context.staging_directory / f"text-{uuid4().hex}.utf8"
        )
        normalized_path.write_bytes(text.encode("utf-8"))

        media_type = SUPPORTED_SUFFIXES[path.suffix.lower()]
        payload = RetrievedPayload(
            logical_key="raw",
            staged_path=raw_path,
            media_type=media_type,
            original_locator=str(path),
            canonical_locator=source.canonical_locator,
            protocol="file",
            response_metadata={
                "file_name": path.name,
                "size_bytes": size,
            },
        )
        representation = RepresentationDraft(
            logical_key="decoded-text",
            staged_path=normalized_path,
            representation_kind="normalized_text",
            media_type="text/plain; charset=utf-8",
            language=request.language,
            parent_payload_key="raw",
            derivation_method="decode_utf8",
            tool_name=self.name,
            tool_version=self.version,
            derivation_parameters={
                "encoding": "utf-8-sig",
                "newline_normalization": False,
            },
            metadata={
                "source_media_type": media_type,
                "source_file_name": path.name,
            },
            text=text,
        )

        return AcquisitionResult(
            canonical_source=source,
            payloads=(payload,),
            representations=(representation,),
        )
