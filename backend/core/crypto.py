"""
密码加密工具模块

使用 Fernet 对称加密算法保护敏感数据。
遵循零硬编码原则，密钥从环境变量读取。
"""
import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from core.config import settings


class PasswordEncryption:
    """密码加密工具类"""

    def __init__(self):
        """初始化加密工具

        从环境变量获取加密密钥，如果不存在则生成一个。
        在生产环境中，必须设置 ENCRYPTION_KEY 环境变量。
        """
        encryption_key = settings.ENCRYPTION_KEY

        if not encryption_key:
            # 开发环境警告
            import warnings
            warnings.warn(
                "ENCRYPTION_KEY 未设置！使用默认密钥仅适用于开发环境。"
                "生产环境必须设置 ENCRYPTION_KEY 环境变量。",
                RuntimeWarning
            )
            # 使用 SECRET_KEY 生成一个稳定的密钥
            encryption_key = self._derive_key_from_password(settings.SECRET_KEY)

        # 确保密钥是有效的 Fernet 密钥
        try:
            self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        except Exception:
            # 如果提供的密钥无效，从其派生一个有效密钥
            self.cipher = Fernet(self._derive_key_from_password(encryption_key))

    def _derive_key_from_password(self, password: str) -> bytes:
        """从密码派生加密密钥

        使用 PBKDF2 算法从密码生成符合 Fernet 要求的密钥。

        Args:
            password: 用于派生密钥的密码

        Returns:
            bytes: 32字节的密钥，base64编码
        """
        if isinstance(password, str):
            password = password.encode()

        # 使用固定的盐值（从 SECRET_KEY 派生）
        # 注意：在生产环境中应该使用随机盐值
        salt = b'talentmail_salt_' + password[:16]

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key

    def encrypt_password(self, password: str) -> str:
        """加密密码

        Args:
            password: 明文密码

        Returns:
            str: 加密后的密码（base64编码）

        Raises:
            ValueError: 如果密码为空
        """
        if not password:
            raise ValueError("密码不能为空")

        # 确保输入是字符串
        if not isinstance(password, str):
            password = str(password)

        # 加密并返回 base64 编码的字符串
        encrypted = self.cipher.encrypt(password.encode())
        return encrypted.decode('utf-8')

    def decrypt_password(self, encrypted_password: str) -> str:
        """解密密码

        Args:
            encrypted_password: 加密的密码（base64编码）

        Returns:
            str: 明文密码

        Raises:
            ValueError: 如果加密密码为空或无效
        """
        if not encrypted_password:
            raise ValueError("加密密码不能为空")

        try:
            # 解密并返回字符串
            decrypted = self.cipher.decrypt(encrypted_password.encode())
            return decrypted.decode('utf-8')
        except Exception as e:
            raise ValueError(f"密码解密失败: {str(e)}")

    @staticmethod
    def generate_encryption_key() -> str:
        """生成新的加密密钥

        用于初始设置或密钥轮换。

        Returns:
            str: 新的 Fernet 密钥
        """
        return Fernet.generate_key().decode('utf-8')


# 全局实例
_encryption_instance: Optional[PasswordEncryption] = None


def get_password_encryption() -> PasswordEncryption:
    """获取密码加密工具的单例实例

    Returns:
        PasswordEncryption: 加密工具实例
    """
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = PasswordEncryption()
    return _encryption_instance


# 便捷函数
def encrypt_password(password: str) -> str:
    """加密密码的便捷函数

    Args:
        password: 明文密码

    Returns:
        str: 加密后的密码
    """
    return get_password_encryption().encrypt_password(password)


def decrypt_password(encrypted_password: str) -> str:
    """解密密码的便捷函数

    Args:
        encrypted_password: 加密的密码

    Returns:
        str: 明文密码
    """
    return get_password_encryption().decrypt_password(encrypted_password)


def generate_encryption_key() -> str:
    """生成新密钥的便捷函数

    Returns:
        str: 新的加密密钥
    """
    return PasswordEncryption.generate_encryption_key()