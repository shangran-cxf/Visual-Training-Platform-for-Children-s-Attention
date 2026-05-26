from utils.password_utils import hash_password, is_bcrypt_hash, verify_password


class TestHashPassword:
    def test_returns_string(self):
        hashed = hash_password("test123")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_different_salts_produce_different_hashes(self):
        h1 = hash_password("test123")
        h2 = hash_password("test123")
        assert h1 != h2

    def test_empty_password(self):
        hashed = hash_password("")
        assert isinstance(hashed, str)

    def test_unicode_password(self):
        hashed = hash_password("密码123")
        assert isinstance(hashed, str)


class TestVerifyPassword:
    def test_correct_password(self):
        hashed = hash_password("secure_password")
        assert verify_password("secure_password", hashed) is True

    def test_wrong_password(self):
        hashed = hash_password("secure_password")
        assert verify_password("wrong_password", hashed) is False

    def test_invalid_hash(self):
        assert verify_password("anything", "not-a-valid-hash") is False

    def test_empty_inputs(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True


class TestIsBcryptHash:
    def test_bcrypt_2b_prefix(self):
        assert is_bcrypt_hash("$2b$12$...") is True

    def test_bcrypt_2a_prefix(self):
        assert is_bcrypt_hash("$2a$12$...") is True

    def test_bcrypt_2y_prefix(self):
        assert is_bcrypt_hash("$2y$12$...") is True

    def test_non_bcrypt_string(self):
        assert is_bcrypt_hash("plain-text") is False

    def test_empty_string(self):
        assert is_bcrypt_hash("") is False
