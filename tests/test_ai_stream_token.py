from app.security.ai_stream_token import (
    create_ai_stream_token,
    verify_ai_stream_token,
)


def test_ai_stream_token_round_trip():
    token = create_ai_stream_token(
        senior_id=123,
        expires_in_seconds=60,
        now=1000,
    )

    claims = verify_ai_stream_token(token, now=1010)

    assert claims is not None
    assert claims.senior_id == 123
    assert claims.expires_at == 1060
    assert claims.nonce


def test_ai_stream_token_rejects_missing_token():
    assert verify_ai_stream_token(None) is None
    assert verify_ai_stream_token("") is None


def test_ai_stream_token_rejects_expired_token():
    token = create_ai_stream_token(
        senior_id=123,
        expires_in_seconds=60,
        now=1000,
    )

    assert verify_ai_stream_token(token, now=1061) is None


def test_ai_stream_token_rejects_tampered_senior_id():
    token = create_ai_stream_token(
        senior_id=123,
        expires_in_seconds=60,
        now=1000,
    )

    tampered = token.replace("123.", "456.", 1)

    assert verify_ai_stream_token(tampered, now=1010) is None


def test_ai_stream_token_rejects_malformed_token():
    assert verify_ai_stream_token("not-a-valid-token") is None
    assert verify_ai_stream_token("1.2.3") is None
    assert verify_ai_stream_token("abc.2.nonce.signature") is None