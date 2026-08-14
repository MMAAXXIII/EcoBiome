from __future__ import annotations

import ast
from pathlib import Path

import pytest

from api.auth.security import hash_password, verify_password

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_password_hash_is_salted_and_verifiable() -> None:
    first_hash = hash_password("mot-de-passe-de-test")
    second_hash = hash_password("mot-de-passe-de-test")

    assert first_hash.startswith("scrypt$")
    assert second_hash.startswith("scrypt$")
    assert first_hash != second_hash
    assert verify_password("mot-de-passe-de-test", first_hash)
    assert not verify_password("mauvais-mot-de-passe", first_hash)


def test_password_hash_rejects_invalid_formats() -> None:
    assert not verify_password("mot-de-passe", "")
    assert not verify_password("mot-de-passe", "sha256$ancien-format")
    assert not verify_password("mot-de-passe", "scrypt$incorrect")


def test_empty_password_is_rejected() -> None:
    with pytest.raises(ValueError):
        hash_password("")


def test_jwt_source_uses_environment_secret_and_specific_exception() -> None:
    path = PROJECT_ROOT / "api" / "auth" / "jwt.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    secret_assignments: list[int] = []
    broad_handlers: list[int] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id == "SECRET":
                    secret_assignments.append(node.lineno)

        if (
            isinstance(node, ast.ExceptHandler)
            and isinstance(node.type, ast.Name)
            and node.type.id == "Exception"
        ):
            broad_handlers.append(node.lineno)

    assert "ECOBIOME_JWT_SECRET" in source
    assert "InvalidTokenError" in source
    assert "ECOBIOME_SECRET_KEY" not in source
    assert not secret_assignments
    assert not broad_handlers
