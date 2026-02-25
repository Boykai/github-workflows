"""Fernet-based encryption for sensitive token storage.

Provides :class:`EncryptionService` for transparent encrypt/decrypt of
GitHub OAuth tokens persisted in SQLite.  When no key is configured the
service operates in *passthrough* mode — plaintext in, plaintext out —
and logs a warning on startup.
"""

from __future__ import annotations

import logging

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class EncryptionService:
    """Singleton-safe Fernet encryption utility.

    Parameters
    ----------
    key:
        A base64-encoded 32-byte Fernet key from the ``ENCRYPTION_KEY``
        environment variable.  If *None*, the service operates in
        passthrough mode (encrypt/decrypt are identity functions).
    """

    def __init__(self, key: str | None = None) -> None:
        self._fernet: Fernet | None = None
        if key:
            try:
                self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
                logger.info("EncryptionService initialised with provided key")
            except Exception:
                logger.exception("Invalid ENCRYPTION_KEY — falling back to passthrough mode")
        else:
            logger.warning(
                "ENCRYPTION_KEY not set — tokens will be stored in plaintext. "
                'Generate a key with: python -c "from cryptography.fernet import Fernet; '
                'print(Fernet.generate_key().decode())"'
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def enabled(self) -> bool:
        """Return *True* if a valid encryption key was provided."""
        return self._fernet is not None

    def encrypt(self, plaintext: str) -> str:
        """Encrypt *plaintext* → Fernet token string (URL-safe base64).

        In passthrough mode returns *plaintext* unchanged.
        """
        if self._fernet is None:
            return plaintext
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt Fernet token → plaintext.

        Handles legacy (pre-encryption) plaintext values gracefully:
        if *ciphertext* looks like a raw GitHub token (``gho_``,
        ``ghp_``, ``ghr_`` prefix) it is returned as-is.

        Raises :class:`ValueError` only on genuinely corrupted
        ciphertext (not legacy plaintext).
        """
        if self._fernet is None:
            return ciphertext

        # Legacy plaintext detection — do not attempt decryption
        if _is_plaintext_token(ciphertext):
            return ciphertext

        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken:
            # Could be a key rotation scenario — treat as expired/invalid
            logger.warning("Failed to decrypt token (key change?) — treating as invalid")
            raise ValueError("Unable to decrypt token — possible key rotation") from None


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

_PLAINTEXT_PREFIXES = ("gho_", "ghp_", "ghr_", "ghu_", "ghs_", "github_pat_")


def _is_plaintext_token(value: str) -> bool:
    """Return *True* if *value* looks like a raw GitHub personal/OAuth token."""
    return any(value.startswith(prefix) for prefix in _PLAINTEXT_PREFIXES)
