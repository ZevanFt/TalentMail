"""验证码提取逻辑测试"""
import pytest


@pytest.fixture(scope="module")
def extract():
    # 延迟导入，确保 conftest 已注入测试环境变量
    from api.pool import extract_verification_code
    return extract_verification_code


class TestExtractVerificationCode:
    def test_chinese_with_colon(self, extract):
        assert extract("您的验证码是：847291") == "847291"

    def test_chinese_without_colon(self, extract):
        assert extract("验证码 483920 五分钟内有效") == "483920"

    def test_english_verification_code(self, extract):
        assert extract("Your verification code is 847291") == "847291"

    def test_english_code_prefix(self, extract):
        assert extract("Code: A8B2C4") == "A8B2C4"

    def test_standalone_digits(self, extract):
        assert extract("请使用 123456 完成登录") == "123456"

    def test_no_code(self, extract):
        assert extract("这是一封普通邮件，没有任何验证码") is None

    def test_empty(self, extract):
        assert extract("") is None

    def test_alphanumeric_code(self, extract):
        assert extract("验证码: Xy9Z") == "Xy9Z"
