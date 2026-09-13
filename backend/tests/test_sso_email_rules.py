"""SSO 邮箱规范化逻辑测试"""
from utils.sso_email import email_match_candidates, normalize_sso_email


class TestNormalizeSsoEmail:
    def test_full_email_kept(self):
        assert normalize_sso_email("alice@example.com", 1, "talent.test") == "alice@example.com"

    def test_bare_username_gets_domain(self):
        assert normalize_sso_email("alice", 1, "talent.test") == "alice@talent.test"

    def test_empty_falls_back_to_sso_id(self):
        assert normalize_sso_email(None, 42, "talent.test") == "sso_42@talent.test"
        assert normalize_sso_email("  ", 42, "talent.test") == "sso_42@talent.test"

    def test_whitespace_trimmed(self):
        assert normalize_sso_email("  bob  ", 1, "talent.test") == "bob@talent.test"


class TestEmailMatchCandidates:
    def test_full_email_single_candidate(self):
        assert email_match_candidates("alice@example.com", "talent.test") == ["alice@example.com"]

    def test_bare_username_two_candidates(self):
        assert email_match_candidates("alice", "talent.test") == ["alice", "alice@talent.test"]

    def test_empty(self):
        assert email_match_candidates("", "talent.test") == []
        assert email_match_candidates(None, "talent.test") == []
