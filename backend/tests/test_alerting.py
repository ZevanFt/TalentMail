"""告警冷却与 Webhook payload 逻辑测试"""
from unittest.mock import Mock, patch

from core.alerting import should_send_alert


class TestAlertCooldown:
    def test_first_alert_allowed(self):
        from core import alerting
        alerting._alert_cooldown.clear()
        assert should_send_alert("unit-test-key") is True

    def test_second_alert_cooled_down(self):
        from core import alerting
        alerting._alert_cooldown.clear()
        assert should_send_alert("unit-test-key-2") is True
        assert should_send_alert("unit-test-key-2") is False

    def test_different_keys_independent(self):
        from core import alerting
        alerting._alert_cooldown.clear()
        assert should_send_alert("key-a") is True
        assert should_send_alert("key-b") is True


class TestSendWebhook:
    def test_no_url_returns_false(self):
        from core import alerting
        alerting._alert_cooldown.clear()
        with patch("core.alerting.settings") as mock_settings:
            mock_settings.ALERT_WEBHOOK_URL = ""
            mock_settings.ALERT_COOLDOWN_SECONDS = 1800
            assert alerting.send_webhook_alert("t", "m") is False

    def test_posts_payload(self):
        from core import alerting
        alerting._alert_cooldown.clear()
        with patch("core.alerting.settings") as mock_settings, \
             patch("core.alerting.httpx.post") as mock_post:
            mock_settings.ALERT_WEBHOOK_URL = "https://hooks.example/x"
            mock_settings.ALERT_COOLDOWN_SECONDS = 1800
            mock_post.return_value = Mock(status_code=200)
            ok = alerting.send_webhook_alert("标题", "内容", level="error", alert_key="k1")
            assert ok is True
            assert mock_post.called
            payload = mock_post.call_args.kwargs["json"]
            assert payload["title"] == "标题"
            assert payload["level"] == "error"
