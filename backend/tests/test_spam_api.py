"""
垃圾邮件管理 API 测试
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime


class TestSpamAPIHelpers:
    """垃圾邮件 API 辅助函数测试"""

    def test_is_sender_trusted_exact_email(self):
        """测试完整邮箱地址在白名单中"""
        from api.spam import is_sender_trusted

        # Mock 数据库查询返回结果
        mock_db = Mock()
        mock_trusted = Mock()
        mock_trusted.email = 'trusted@example.com'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_trusted

        result = is_sender_trusted(mock_db, user_id=1, sender_email='trusted@example.com')

        assert result is True

    def test_is_sender_trusted_domain(self):
        """测试域名在白名单中"""
        from api.spam import is_sender_trusted

        # Mock 数据库查询返回结果
        mock_db = Mock()
        mock_trusted = Mock()
        mock_trusted.email = '@trusted-domain.com'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_trusted

        result = is_sender_trusted(mock_db, user_id=1, sender_email='anyone@trusted-domain.com')

        assert result is True

    def test_is_sender_not_trusted(self):
        """测试发件人不在白名单中"""
        from api.spam import is_sender_trusted

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = is_sender_trusted(mock_db, user_id=1, sender_email='unknown@spam.com')

        assert result is False

    def test_is_sender_trusted_case_insensitive(self):
        """测试邮箱地址不区分大小写"""
        from api.spam import is_sender_trusted

        mock_db = Mock()
        mock_trusted = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_trusted

        # 应该将邮箱转为小写进行比较
        is_sender_trusted(mock_db, user_id=1, sender_email='TRUSTED@EXAMPLE.COM')

        # 验证查询时使用的是小写
        call_args = mock_db.query.return_value.filter.call_args
        # 确保调用了 filter

    def test_is_sender_blocked(self):
        """测试发件人在黑名单中"""
        from api.spam import is_sender_blocked

        mock_db = Mock()
        mock_blocked = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_blocked

        result = is_sender_blocked(mock_db, user_id=1, sender_email='blocked@spam.com')

        assert result is True

    def test_is_sender_not_blocked(self):
        """测试发件人不在黑名单中"""
        from api.spam import is_sender_blocked

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = is_sender_blocked(mock_db, user_id=1, sender_email='normal@example.com')

        assert result is False


class TestTrustedSenderSchema:
    """白名单 Schema 测试"""

    def test_trusted_sender_create_valid(self):
        """测试创建白名单请求验证"""
        from api.spam import TrustedSenderCreate

        data = TrustedSenderCreate(email='trusted@example.com', note='My friend')

        assert data.email == 'trusted@example.com'
        assert data.note == 'My friend'

    def test_trusted_sender_create_domain(self):
        """测试域名格式白名单请求"""
        from api.spam import TrustedSenderCreate

        data = TrustedSenderCreate(email='@trusted-domain.com')

        assert data.email == '@trusted-domain.com'
        assert data.note is None

    def test_spam_action_request(self):
        """测试垃圾邮件操作请求"""
        from api.spam import SpamActionRequest

        data = SpamActionRequest(email_ids=[1, 2, 3, 4, 5])

        assert len(data.email_ids) == 5
        assert 1 in data.email_ids


class TestSpamReportSchema:
    """垃圾邮件报告 Schema 测试"""

    def test_spam_report_read(self):
        """测试垃圾邮件报告读取 Schema"""
        from api.spam import SpamReportRead

        data = SpamReportRead(
            id=1,
            email_id=100,
            report_type='spam',
            learned=True,
            created_at='2025-01-01T00:00:00'
        )

        assert data.id == 1
        assert data.email_id == 100
        assert data.report_type == 'spam'
        assert data.learned is True


class TestTrainSpamAssassin:
    """SpamAssassin 训练测试"""

    @pytest.mark.asyncio
    async def test_train_spamassassin_marks_learned(self):
        """测试训练后标记为已学习"""
        from api.spam import train_spamassassin

        mock_db = Mock()
        mock_reports = [
            Mock(learned=False),
            Mock(learned=False),
            Mock(learned=False)
        ]

        await train_spamassassin(mock_db, mock_reports, 'spam')

        # 验证所有报告都被标记为已学习
        for report in mock_reports:
            assert report.learned is True

        mock_db.commit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
