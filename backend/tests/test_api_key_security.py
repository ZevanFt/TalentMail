from core.api_keys import (
    extract_api_key_prefix,
    generate_api_key,
    hash_api_key,
    verify_api_key,
)


def test_hash_and_verify_api_key():
    raw_key = "tm_example_key_for_test_only"
    key_hash = hash_api_key(raw_key)

    assert verify_api_key(raw_key, key_hash) is True
    assert verify_api_key("tm_wrong_key", key_hash) is False


def test_generate_api_key_returns_expected_tuple():
    raw_key, key_prefix, key_hash = generate_api_key()

    assert raw_key.startswith("tm_")
    assert key_prefix == extract_api_key_prefix(raw_key)
    assert verify_api_key(raw_key, key_hash) is True
