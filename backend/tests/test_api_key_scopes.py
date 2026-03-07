import pytest
from fastapi import HTTPException

from api.deps import require_api_key_scopes


class DummyApiKey:
    def __init__(self, scopes):
        self.scopes = scopes


def test_require_api_key_scopes_passes_when_scopes_present():
    dependency = require_api_key_scopes(["temp_mailbox:create", "temp_email:read"])
    api_key = DummyApiKey(scopes=["temp_email:read", "temp_mailbox:create", "temp_code:read"])

    result = dependency(api_key=api_key)

    assert result is api_key


def test_require_api_key_scopes_raises_403_when_scope_missing():
    dependency = require_api_key_scopes(["temp_mailbox:restore"])
    api_key = DummyApiKey(scopes=["temp_mailbox:read"])

    with pytest.raises(HTTPException) as exc_info:
        dependency(api_key=api_key)

    assert exc_info.value.status_code == 403
    assert "temp_mailbox:restore" in exc_info.value.detail
