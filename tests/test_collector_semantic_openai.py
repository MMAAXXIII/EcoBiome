from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Self

import pytest

from ecobiome.knowledge_acquisition.collector_acquire import acquire_source
from ecobiome.knowledge_acquisition.collector_cli import main as collector_main
from ecobiome.knowledge_acquisition.persistence import CollectorStore
from ecobiome.knowledge_acquisition.semantic_extraction import (
    atomic_batch_to_payload,
    run_semantic_extractor,
)
from ecobiome.knowledge_acquisition.semantic_openai import (
    OpenAIResponsesSemanticExtractor,
    OpenAISemanticExtractionError,
    RequestsOpenAIResponsesTransport,
)


class _FakeTransport:
    def __init__(self, mode: str = "valid") -> None:
        self.mode = mode
        self.calls: list[dict[str, object]] = []

    def create_response(
        self,
        *,
        api_key: str,
        payload: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, str]]:
        self.calls.append(
            {
                "api_key": api_key,
                "payload": payload,
            }
        )
        input_items = payload["input"]
        assert isinstance(input_items, list)
        user = input_items[1]
        assert isinstance(user, dict)
        content = user["content"]
        assert isinstance(content, list)
        text = content[0]["text"]
        request = json.loads(str(text))
        source_claim = request["source_claims"][0]
        evidence = source_claim["evidence"]

        if self.mode == "zero":
            model_payload: dict[str, object] = {"proposals": []}
        elif self.mode == "bad_evidence":
            model_payload = {
                "proposals": [
                    {
                        "source_claim_id": source_claim["claim_id"],
                        "text": "La source indique une observation vérifiable.",
                        "semantic_type": "observation",
                        "evidence_ids": [
                            "00000000-0000-4000-8000-000000000000"
                        ],
                    }
                ]
            }
        elif self.mode == "duplicate":
            proposal = {
                "source_claim_id": source_claim["claim_id"],
                "text": "La source indique une observation vérifiable.",
                "semantic_type": "observation",
                "evidence_ids": [evidence[0]["evidence_id"]],
            }
            model_payload = {"proposals": [proposal, proposal]}
        else:
            model_payload = {
                "proposals": [
                    {
                        "source_claim_id": source_claim["claim_id"],
                        "text": "La source indique une observation vérifiable.",
                        "semantic_type": "observation",
                        "evidence_ids": [evidence[0]["evidence_id"]],
                    }
                ]
            }

        response = {
            "id": "resp_test",
            "status": "completed",
            "model": payload["model"],
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": json.dumps(model_payload),
                        }
                    ],
                }
            ],
            "usage": {
                "input_tokens": 123,
                "output_tokens": 45,
                "total_tokens": 168,
            },
        }
        return response, {"x-request-id": "req_test"}


def _source_claim(
    tmp_path: Path,
) -> tuple[CollectorStore, dict[str, object]]:
    source = tmp_path / "source.txt"
    source.write_text(
        "La source présente le poisson comme robuste.",
        encoding="utf-8",
    )
    database = tmp_path / "collector.sqlite3"
    acquired = acquire_source(
        source=str(source),
        database=database,
        maximum_passage_characters=1000,
    )
    representation_id = (
        acquired.receipt.representations[0].representation_id
    )
    store = CollectorStore(database)
    receipt = store.propose_source_statement_claims(
        representation_id=representation_id,
    )
    assert len(receipt.claims) == 1
    claim = store.get_claim_with_evidence(receipt.claims[0].claim_id)
    return store, claim


def test_openai_extractor_builds_strict_nonpersisting_request(
    tmp_path: Path,
) -> None:
    store, claim = _source_claim(tmp_path)
    before = store.summary()["claims"]
    transport = _FakeTransport()
    extractor = OpenAIResponsesSemanticExtractor(
        model="gpt-5-mini",
        api_key="test-secret-key",
        transport=transport,
    )

    run = run_semantic_extractor(
        store,
        extractor,
        [str(claim["id"])],
    )
    payload = atomic_batch_to_payload(run.batch)

    assert len(transport.calls) == 1
    call = transport.calls[0]
    assert call["api_key"] == "test-secret-key"
    api_payload = call["payload"]
    assert api_payload["model"] == "gpt-5-mini"
    assert api_payload["store"] is False
    assert api_payload["tools"] == []

    text_config = api_payload["text"]
    assert isinstance(text_config, dict)
    output_format = text_config["format"]
    assert output_format["type"] == "json_schema"
    assert output_format["strict"] is True

    proposal = payload["proposals"][0]
    assert proposal["source_claim_id"] == claim["id"]
    assert proposal["qualifiers"]["benchmark_only"] is True
    assert proposal["qualifiers"]["provider"] == "openai"
    assert proposal["qualifiers"]["model"] == "gpt-5-mini"
    assert store.summary()["claims"] == before

    diagnostics = extractor.last_diagnostics
    assert diagnostics is not None
    assert diagnostics["request_id"] == "req_test"
    assert diagnostics["store"] is False
    assert diagnostics["tools_enabled"] is False
    assert diagnostics["usage"]["total_tokens"] == 168
    assert "test-secret-key" not in json.dumps(diagnostics)


def test_openai_extractor_accepts_zero_proposals(
    tmp_path: Path,
) -> None:
    store, claim = _source_claim(tmp_path)
    extractor = OpenAIResponsesSemanticExtractor(
        api_key="test-secret-key",
        transport=_FakeTransport("zero"),
    )

    run = run_semantic_extractor(
        store,
        extractor,
        [str(claim["id"])],
    )

    assert run.batch.proposals == ()


def test_openai_extractor_rejects_evidence_outside_parent(
    tmp_path: Path,
) -> None:
    store, claim = _source_claim(tmp_path)
    extractor = OpenAIResponsesSemanticExtractor(
        api_key="test-secret-key",
        transport=_FakeTransport("bad_evidence"),
    )

    with pytest.raises(
        OpenAISemanticExtractionError,
        match="outside its parent Claim",
    ):
        run_semantic_extractor(
            store,
            extractor,
            [str(claim["id"])],
        )


def test_openai_extractor_rejects_duplicate_model_proposal(
    tmp_path: Path,
) -> None:
    store, claim = _source_claim(tmp_path)
    extractor = OpenAIResponsesSemanticExtractor(
        api_key="test-secret-key",
        transport=_FakeTransport("duplicate"),
    )

    with pytest.raises(
        OpenAISemanticExtractionError,
        match="duplicate proposal",
    ):
        run_semantic_extractor(
            store,
            extractor,
            [str(claim["id"])],
        )


def test_openai_extractor_requires_api_key_before_transport(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, claim = _source_claim(tmp_path)
    transport = _FakeTransport()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    extractor = OpenAIResponsesSemanticExtractor(
        transport=transport,
    )

    with pytest.raises(
        OpenAISemanticExtractionError,
        match="OPENAI_API_KEY",
    ):
        run_semantic_extractor(
            store,
            extractor,
            [str(claim["id"])],
        )

    assert transport.calls == []


def test_openai_model_identifier_is_validated() -> None:
    with pytest.raises(ValueError, match="model identifier"):
        OpenAIResponsesSemanticExtractor(
            model="https://attacker.invalid/model",
            api_key="test-secret-key",
            transport=_FakeTransport(),
        )


class _FakeResponse:
    def __init__(
        self,
        *,
        status_code: int,
        body: bytes,
        content_type: str = "application/json",
    ) -> None:
        self.status_code = status_code
        self._body = body
        self.headers = {
            "Content-Type": content_type,
            "Content-Length": str(len(body)),
            "x-request-id": "req_transport",
        }

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def iter_content(self, chunk_size: int) -> list[bytes]:
        assert chunk_size > 0
        return [self._body]


class _FakeSession:
    def __init__(self, response: _FakeResponse) -> None:
        self.response = response
        self.trust_env = True
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def post(self, url: str, **kwargs: object) -> _FakeResponse:
        self.calls.append((url, kwargs))
        return self.response


def test_requests_transport_uses_fixed_endpoint_and_no_redirects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = json.dumps(
        {
            "id": "resp",
            "status": "completed",
            "output": [],
        }
    ).encode("utf-8")
    session = _FakeSession(
        _FakeResponse(status_code=200, body=body)
    )
    monkeypatch.setattr(
        "ecobiome.knowledge_acquisition.semantic_openai.requests.Session",
        lambda: session,
    )

    transport = RequestsOpenAIResponsesTransport()
    parsed, headers = transport.create_response(
        api_key="secret-value",
        payload={"model": "gpt-5-mini"},
    )

    assert parsed["id"] == "resp"
    assert headers["x-request-id"] == "req_transport"
    assert session.trust_env is False
    assert len(session.calls) == 1
    url, kwargs = session.calls[0]
    assert url == "https://api.openai.com/v1/responses"
    assert kwargs["allow_redirects"] is False
    assert kwargs["stream"] is True
    request_headers = kwargs["headers"]
    assert request_headers["Authorization"] == "Bearer secret-value"


def test_requests_transport_redacts_key_from_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "secret-value"
    body = json.dumps(
        {
            "error": {
                "message": f"request failed with {secret}",
            }
        }
    ).encode("utf-8")
    session = _FakeSession(
        _FakeResponse(status_code=400, body=body)
    )
    monkeypatch.setattr(
        "ecobiome.knowledge_acquisition.semantic_openai.requests.Session",
        lambda: session,
    )

    with pytest.raises(OpenAISemanticExtractionError) as caught:
        RequestsOpenAIResponsesTransport().create_response(
            api_key=secret,
            payload={"model": "gpt-5-mini"},
        )

    message = str(caught.value)
    assert secret not in message
    assert "[REDACTED]" in message


def test_cli_semantic_openai_is_wired_and_fails_without_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, claim = _source_claim(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(
        OpenAISemanticExtractionError,
        match="OPENAI_API_KEY",
    ):
        collector_main(
            [
                "semantic-openai",
                "--database",
                str(store.database_path),
                "--claim-id",
                str(claim["id"]),
            ]
        )
