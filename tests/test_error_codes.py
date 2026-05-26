from utils.error_codes import (
    ACTIVE_SESSION_EXISTS,
    AUTH_ERROR,
    BAD_REQUEST,
    CHILD_NOT_BELONG,
    DATABASE_ERROR,
    DUPLICATE_ENTRY,
    ERROR_MESSAGES,
    HTTP_STATUS_MAP,
    INTERNAL_ERROR,
    NOT_FOUND,
    PERMISSION_DENIED,
    RATE_LIMIT_EXCEEDED,
    RESOURCE_NOT_FOUND,
    SESSION_EXPIRED,
    SESSION_NOT_FOUND,
    TOKEN_EXPIRED,
    TOKEN_INVALID,
    USER_NOT_FOUND,
    VALIDATION_ERROR,
)


class TestErrorCodes:
    def test_all_codes_have_messages(self):
        codes = [
            AUTH_ERROR,
            PERMISSION_DENIED,
            NOT_FOUND,
            VALIDATION_ERROR,
            DATABASE_ERROR,
            BAD_REQUEST,
            INTERNAL_ERROR,
            TOKEN_EXPIRED,
            TOKEN_INVALID,
            RESOURCE_NOT_FOUND,
            USER_NOT_FOUND,
            DUPLICATE_ENTRY,
            RATE_LIMIT_EXCEEDED,
            SESSION_NOT_FOUND,
            SESSION_EXPIRED,
            CHILD_NOT_BELONG,
            ACTIVE_SESSION_EXISTS,
        ]
        for code in codes:
            assert code in ERROR_MESSAGES, f"Missing message for {code}"

    def test_all_codes_have_http_status(self):
        codes = ERROR_MESSAGES.keys()
        for code in codes:
            assert code in HTTP_STATUS_MAP, f"Missing HTTP status for {code}"

    def test_all_http_statuses_are_valid(self):
        valid_statuses = {200, 201, 204, 400, 401, 403, 404, 409, 410, 422, 429, 500}
        for code, status in HTTP_STATUS_MAP.items():
            assert status in valid_statuses, f"Invalid HTTP status {status} for {code}"

    def test_auth_error_is_401(self):
        assert HTTP_STATUS_MAP[AUTH_ERROR] == 401

    def test_permission_denied_is_403(self):
        assert HTTP_STATUS_MAP[PERMISSION_DENIED] == 403

    def test_not_found_is_404(self):
        assert HTTP_STATUS_MAP[NOT_FOUND] == 404

    def test_duplicate_is_409(self):
        assert HTTP_STATUS_MAP[DUPLICATE_ENTRY] == 409

    def test_rate_limit_is_429(self):
        assert HTTP_STATUS_MAP[RATE_LIMIT_EXCEEDED] == 429
