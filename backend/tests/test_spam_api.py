"""
垃圾邮件 API 测试
"""
import pytest
from types import SimpleNamespace
from unittest.mock import Mock


class TestSpamAPIHelpers:
    """垃圾邮件 API 辅助函数测试"""

    def test_is_sender_trusted_exact_email(self):
        from api.spam import is_sender_trusted

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = Mock(email="trusted@example.com")

        assert is_sender_trusted(mock_db, user_id=1, sender_email="trusted@example.com") is True

    def test_is_sender_trusted_domain(self):
        from api.spam import is_sender_trusted

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = Mock(email="@trusted-domain.com")

        assert is_sender_trusted(mock_db, user_id=1, sender_email="anyone@trusted-domain.com") is True

    def test_is_sender_not_trusted(self):
        from api.spam import is_sender_trusted

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        assert is_sender_trusted(mock_db, user_id=1, sender_email="unknown@spam.com") is False

    def test_is_sender_blocked(self):
        from api.spam import is_sender_blocked

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = Mock(email="blocked@spam.com")

        assert is_sender_blocked(mock_db, user_id=1, sender_email="blocked@spam.com") is True

    def test_is_sender_not_blocked(self):
        from api.spam import is_sender_blocked

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        assert is_sender_blocked(mock_db, user_id=1, sender_email="normal@example.com") is False


class TestTrainSpamAssassin:
    """SpamAssassin 训练任务测试"""

    @pytest.mark.asyncio
    async def test_train_spamassassin_retries_then_success(self):
        from api.spam import train_spamassassin

        report = SimpleNamespace(
            id=11,
            report_type="spam",
            learned=False,
            learn_attempts=0,
            learn_error=None,
            learned_at=None,
        )

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.all.return_value = [report]
        mock_db.query.return_value.filter.return_value.count.return_value = 1

        trainer = Mock(side_effect=[RuntimeError("first fail"), None])

        await train_spamassassin(
            [11],
            "spam",
            session_factory=lambda: mock_db,
            trainer=trainer,
            max_retries=2,
            retry_delay_seconds=0,
        )

        assert report.learned is True
        assert report.learn_attempts == 2
        assert report.learn_error is None
        assert report.learned_at is not None
        assert trainer.call_count == 2
        assert mock_db.commit.call_count >= 1

    @pytest.mark.asyncio
    async def test_train_spamassassin_all_retries_failed(self):
        from api.spam import train_spamassassin

        report = SimpleNamespace(
            id=12,
            report_type="ham",
            learned=False,
            learn_attempts=0,
            learn_error=None,
            learned_at=None,
        )

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.all.return_value = [report]
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        trainer = Mock(side_effect=RuntimeError("sa-learn failed"))

        await train_spamassassin(
            [12],
            "ham",
            session_factory=lambda: mock_db,
            trainer=trainer,
            max_retries=3,
            retry_delay_seconds=0,
        )

        assert report.learned is False
        assert report.learn_attempts == 3
        assert "sa-learn failed" in (report.learn_error or "")
        assert report.learned_at is None
        assert trainer.call_count == 3


class TestSpamAssassinContentBuilder:
    def test_build_eml_content_prefers_text_and_falls_back_html(self):
        from core.spamassassin import _build_eml_content

        report = SimpleNamespace(
            id=1,
            email=SimpleNamespace(
                subject="Test Subject",
                sender="alice@example.com",
                recipients="bob@example.com",
                body_text="",
                body_html="<p>Hello <b>World</b></p>",
            ),
        )

        content = _build_eml_content(report).decode("utf-8")

        assert "Subject: Test Subject" in content
        assert "From: alice@example.com" in content
        assert "To: bob@example.com" in content
        assert "Hello World" in content
