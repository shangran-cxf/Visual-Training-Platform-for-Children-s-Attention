from middleware.auth_middleware import generate_token, verify_token


class TestGenerateToken:
    def test_returns_string(self):
        token = generate_token(1, "parent")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_different_users_different_tokens(self):
        token1 = generate_token(1, "parent")
        token2 = generate_token(2, "parent")
        assert token1 != token2

    def test_different_roles_different_tokens(self):
        token1 = generate_token(1, "parent")
        token2 = generate_token(1, "admin")
        assert token1 != token2


class TestVerifyToken:
    def test_valid_token_returns_payload(self):
        token = generate_token(42, "parent")
        payload = verify_token(token)
        assert payload is not None
        assert payload["user_id"] == 42
        assert payload["role"] == "parent"

    def test_invalid_token_returns_none(self):
        assert verify_token("invalid-token-string") is None

    def test_empty_string_returns_none(self):
        assert verify_token("") is None

    def test_admin_role(self):
        token = generate_token(1, "admin")
        payload = verify_token(token)
        assert payload["role"] == "admin"
