from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import secrets

_SCHEME = "scrypt"
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SALT_SIZE = 16
_DERIVED_KEY_SIZE = 64


def _encode_bytes(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii")


def _decode_bytes(value: str) -> bytes:
    return base64.urlsafe_b64decode(value.encode("ascii"))


def _derive_password_key(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_DERIVED_KEY_SIZE,
    )


def hash_password(password: str) -> str:
    if not isinstance(password, str) or not password:
        raise ValueError("Le mot de passe ne peut pas être vide.")

    salt = secrets.token_bytes(_SALT_SIZE)
    derived_key = _derive_password_key(password, salt)

    return "$".join(
        (
            _SCHEME,
            str(_SCRYPT_N),
            str(_SCRYPT_R),
            str(_SCRYPT_P),
            _encode_bytes(salt),
            _encode_bytes(derived_key),
        )
    )


def verify_password(password: str, encoded_hash: str) -> bool:
    if not isinstance(password, str) or not isinstance(encoded_hash, str):
        return False

    try:
        scheme, n_text, r_text, p_text, salt_text, digest_text = (
            encoded_hash.split("$", 5)
        )

        if scheme != _SCHEME:
            return False

        if (
            int(n_text) != _SCRYPT_N
            or int(r_text) != _SCRYPT_R
            or int(p_text) != _SCRYPT_P
        ):
            return False

        salt = _decode_bytes(salt_text)
        expected_digest = _decode_bytes(digest_text)
        actual_digest = _derive_password_key(password, salt)
    except (ValueError, TypeError, binascii.Error):
        return False

    return hmac.compare_digest(actual_digest, expected_digest)
