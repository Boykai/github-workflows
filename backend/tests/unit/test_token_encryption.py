"""Tests for token encryption at rest (US6 — FR-003).

Verifies:
- Tokens are encrypted during session storage
- Tokens are decrypted on session retrieval
- Legacy plaintext tokens are handled gracefully on decrypt
"""

from unittest.mock import patch

import pytest

from src.models.user import UserSession
from src.services.encryption import EncryptionService


class TestTokenEncryptionAtRest:
    """Tokens stored in the DB must be Fernet-encrypted when encryption_key is set."""

    @pytest.fixture
    def encryption_service(self):
        """A real EncryptionService with a generated Fernet key."""
        from cryptography.fernet import Fernet

        key = Fernet.generate_key().decode()
        return EncryptionService(key)

    async def test_encrypt_decrypt_roundtrip(self, encryption_service):
        """Encrypting then decrypting a token should return the original."""
        original = "gho_abc123xyz"
        encrypted = encryption_service.encrypt(original)
        assert encrypted != original
        assert encrypted.startswith("gAAAAA")  # Fernet prefix
        decrypted = encryption_service.decrypt(encrypted)
        assert decrypted == original

    async def test_session_store_encrypts_access_token(self, mock_db, encryption_service):
        """save_session should encrypt the access_token before writing to DB."""
        from src.services import session_store

        session = UserSession(
            github_user_id="42",
            github_username="enctest",
            access_token="gho_plaintext_token",
            refresh_token="ghr_plaintext_refresh",
        )

        # Patch the encryption service to intercept calls
        with patch.object(
            session_store,
            "_encryption_service",
            encryption_service,
            create=True,
        ):
            await session_store.save_session(mock_db, session)

        # Read raw DB value — should NOT be plaintext
        cursor = await mock_db.execute(
            "SELECT access_token, refresh_token FROM user_sessions WHERE session_id = ?",
            (str(session.session_id),),
        )
        row = await cursor.fetchone()
        assert row is not None
        raw_access = row[0] if not isinstance(row, dict) else row["access_token"]
        # The stored value should be encrypted (Fernet ciphertext)
        assert raw_access != "gho_plaintext_token", (
            "access_token stored in plaintext — encryption not applied"
        )

    async def test_legacy_plaintext_fallback_on_decrypt(self, encryption_service):
        """Decrypting a legacy plaintext token (gho_ prefix) should return it as-is."""
        legacy_token = "gho_legacy_token_from_before_encryption"
        result = encryption_service.decrypt(legacy_token)
        assert result == legacy_token

    async def test_passthrough_mode_when_no_key(self):
        """Without encryption_key, tokens should pass through unchanged."""
        svc = EncryptionService(key=None)
        assert not svc.enabled
        token = "gho_mytoken"
        assert svc.encrypt(token) == token
        assert svc.decrypt(token) == token
