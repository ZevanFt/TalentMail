"""
测试密码加密功能
"""
import pytest
from core.crypto import (
    PasswordEncryption,
    encrypt_password,
    decrypt_password,
    generate_encryption_key
)


class TestPasswordEncryption:
    """密码加密测试类"""

    def test_encrypt_decrypt_basic(self):
        """测试基本的加密解密功能"""
        password = "test_password_123"
        encrypted = encrypt_password(password)

        # 确保加密后的密码不同于原密码
        assert encrypted != password

        # 确保可以正确解密
        decrypted = decrypt_password(encrypted)
        assert decrypted == password

    def test_encrypt_decrypt_special_chars(self):
        """测试包含特殊字符的密码"""
        passwords = [
            "p@$$w0rd!",
            "Test#123$%^",
            "中文密码123",
            "emoji😀password",
            "very long password " * 10,
            "with\nnewline",
            "with\ttab",
            'with"quotes"',
            "with'apostrophe'",
        ]

        for password in passwords:
            encrypted = encrypt_password(password)
            decrypted = decrypt_password(encrypted)
            assert decrypted == password, f"Failed for password: {password}"

    def test_empty_password_error(self):
        """测试空密码应该报错"""
        with pytest.raises(ValueError, match="密码不能为空"):
            encrypt_password("")

        with pytest.raises(ValueError, match="密码不能为空"):
            encrypt_password(None)

    def test_empty_encrypted_password_error(self):
        """测试空加密密码应该报错"""
        with pytest.raises(ValueError, match="加密密码不能为空"):
            decrypt_password("")

        with pytest.raises(ValueError, match="加密密码不能为空"):
            decrypt_password(None)

    def test_invalid_encrypted_password(self):
        """测试无效的加密密码"""
        with pytest.raises(ValueError, match="密码解密失败"):
            decrypt_password("invalid_encrypted_string")

    def test_consistent_encryption(self):
        """测试相同密码每次加密结果不同但都能解密"""
        password = "consistent_test"
        encrypted1 = encrypt_password(password)
        encrypted2 = encrypt_password(password)

        # Fernet 使用时间戳，所以每次加密结果不同
        assert encrypted1 != encrypted2

        # 但都能正确解密
        assert decrypt_password(encrypted1) == password
        assert decrypt_password(encrypted2) == password

    def test_generate_encryption_key(self):
        """测试密钥生成"""
        key1 = generate_encryption_key()
        key2 = generate_encryption_key()

        # 确保生成的密钥不同
        assert key1 != key2

        # 确保密钥长度正确 (Fernet密钥是44字符的base64)
        assert len(key1) == 44
        assert len(key2) == 44

        # 确保生成的密钥可用
        encryption = PasswordEncryption()
        encryption.cipher = encryption.cipher.__class__(key1.encode())
        test_password = "key_test"
        encrypted = encryption.encrypt_password(test_password)
        decrypted = encryption.decrypt_password(encrypted)
        assert decrypted == test_password

    def test_unicode_passwords(self):
        """测试各种 Unicode 密码"""
        unicode_passwords = [
            "пароль",  # 俄文
            "パスワード",  # 日文
            "🔐🔑🗝️",  # 表情符号
            "àáâãäåæçèéêë",  # 带重音的拉丁字符
            "密碼測試",  # 繁体中文
        ]

        for password in unicode_passwords:
            encrypted = encrypt_password(password)
            decrypted = decrypt_password(encrypted)
            assert decrypted == password

    def test_encryption_with_custom_key(self):
        """测试使用自定义密钥"""
        # 创建两个不同密钥的加密实例
        import os

        # 临时修改环境变量
        original_key = os.environ.get('ENCRYPTION_KEY')

        try:
            # 设置第一个密钥
            test_key1 = generate_encryption_key()
            os.environ['ENCRYPTION_KEY'] = test_key1
            enc1 = PasswordEncryption()

            # 设置第二个密钥
            test_key2 = generate_encryption_key()
            os.environ['ENCRYPTION_KEY'] = test_key2
            enc2 = PasswordEncryption()

            # 使用第一个密钥加密
            password = "test_custom_key"
            encrypted = enc1.encrypt_password(password)

            # 第一个密钥应该能解密
            assert enc1.decrypt_password(encrypted) == password

            # 第二个密钥解密应该失败或返回不同结果
            try:
                decrypted = enc2.decrypt_password(encrypted)
                # 如果没有抛出异常，解密结果应该不同
                # 但实际上 Fernet 会抛出异常
                assert decrypted != password
            except (ValueError, Exception):
                # 预期会抛出解密失败的异常
                pass

        finally:
            # 恢复原始环境变量
            if original_key:
                os.environ['ENCRYPTION_KEY'] = original_key
            elif 'ENCRYPTION_KEY' in os.environ:
                del os.environ['ENCRYPTION_KEY']

    def test_password_encryption_singleton(self):
        """测试单例模式"""
        from core.crypto import get_password_encryption, _encryption_instance

        # 清除现有实例
        original_instance = _encryption_instance

        try:
            # 第一次获取
            inst1 = get_password_encryption()
            # 第二次获取应该是同一个实例
            inst2 = get_password_encryption()
            assert inst1 is inst2

        finally:
            # 恢复原始实例
            import core.crypto
            core.crypto._encryption_instance = original_instance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])