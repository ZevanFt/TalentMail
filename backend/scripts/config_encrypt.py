#!/usr/bin/env python3
"""
配置加密工具

用于加密和解密 .env 文件中的敏感配置值。
支持的敏感配置项：
- SECRET_KEY
- POSTGRES_PASSWORD
- ADMIN_PASSWORD
- DEFAULT_MAIL_PASSWORD
- RSPAMD_PASSWORD
- ENCRYPTION_KEY

使用方法:
    # 加密单个值
    python config_encrypt.py encrypt "my_secret_value"

    # 解密单个值
    python config_encrypt.py decrypt "encrypted_value"

    # 加密整个 .env 文件中的敏感配置
    python config_encrypt.py encrypt-file /path/to/.env

    # 生成新的加密密钥
    python config_encrypt.py generate-key

    # 验证加密配置
    python config_encrypt.py verify
"""
import os
import sys
import re
import argparse

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.crypto import encrypt_password, decrypt_password, generate_encryption_key


# 需要加密的敏感配置项列表
SENSITIVE_KEYS = [
    'POSTGRES_PASSWORD',
    'ADMIN_PASSWORD',
    'DEFAULT_MAIL_PASSWORD',
    'RSPAMD_PASSWORD',
]

# 加密值的前缀标识
ENCRYPTED_PREFIX = 'ENC:'


def is_encrypted(value: str) -> bool:
    """检查值是否已加密"""
    return value.startswith(ENCRYPTED_PREFIX)


def encrypt_value(value: str) -> str:
    """加密值"""
    if not value or is_encrypted(value):
        return value
    encrypted = encrypt_password(value)
    return f"{ENCRYPTED_PREFIX}{encrypted}"


def decrypt_value(value: str) -> str:
    """解密值"""
    if not value or not is_encrypted(value):
        return value
    encrypted_part = value[len(ENCRYPTED_PREFIX):]
    return decrypt_password(encrypted_part)


def encrypt_env_file(env_path: str, output_path: str = None) -> dict:
    """加密 .env 文件中的敏感配置

    Args:
        env_path: 源 .env 文件路径
        output_path: 输出文件路径，默认覆盖源文件

    Returns:
        dict: 加密统计信息
    """
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"文件不存在: {env_path}")

    output_path = output_path or env_path
    encrypted_count = 0
    skipped_count = 0

    lines = []
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()

            # 跳过空行和注释
            if not stripped or stripped.startswith('#'):
                lines.append(line)
                continue

            # 解析键值对
            match = re.match(r'^([A-Z_]+)=(.*)$', stripped)
            if not match:
                lines.append(line)
                continue

            key, value = match.groups()

            # 检查是否是敏感配置
            if key in SENSITIVE_KEYS and value and not is_encrypted(value):
                encrypted_value = encrypt_value(value)
                lines.append(f"{key}={encrypted_value}\n")
                encrypted_count += 1
                print(f"  [加密] {key}")
            else:
                lines.append(line)
                if key in SENSITIVE_KEYS:
                    if is_encrypted(value):
                        print(f"  [跳过] {key} (已加密)")
                    elif not value:
                        print(f"  [跳过] {key} (空值)")
                    skipped_count += 1

    # 写入输出文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    return {
        'encrypted': encrypted_count,
        'skipped': skipped_count,
        'output': output_path
    }


def decrypt_env_file(env_path: str, output_path: str = None) -> dict:
    """解密 .env 文件中的加密配置

    Args:
        env_path: 源 .env 文件路径
        output_path: 输出文件路径，默认覆盖源文件

    Returns:
        dict: 解密统计信息
    """
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"文件不存在: {env_path}")

    output_path = output_path or env_path
    decrypted_count = 0

    lines = []
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()

            # 跳过空行和注释
            if not stripped or stripped.startswith('#'):
                lines.append(line)
                continue

            # 解析键值对
            match = re.match(r'^([A-Z_]+)=(.*)$', stripped)
            if not match:
                lines.append(line)
                continue

            key, value = match.groups()

            # 检查是否是加密值
            if is_encrypted(value):
                try:
                    decrypted_value = decrypt_value(value)
                    lines.append(f"{key}={decrypted_value}\n")
                    decrypted_count += 1
                    print(f"  [解密] {key}")
                except Exception as e:
                    print(f"  [失败] {key}: {e}")
                    lines.append(line)
            else:
                lines.append(line)

    # 写入输出文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    return {
        'decrypted': decrypted_count,
        'output': output_path
    }


def verify_config() -> bool:
    """验证加密配置是否正确"""
    print("验证加密配置...")

    # 测试加密解密
    test_value = "test_password_123"
    try:
        encrypted = encrypt_password(test_value)
        decrypted = decrypt_password(encrypted)

        if decrypted == test_value:
            print("  [✓] 加密解密测试通过")
            return True
        else:
            print("  [✗] 加密解密结果不匹配")
            return False
    except Exception as e:
        print(f"  [✗] 加密测试失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='配置加密工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # encrypt 命令
    encrypt_parser = subparsers.add_parser('encrypt', help='加密单个值')
    encrypt_parser.add_argument('value', help='要加密的值')

    # decrypt 命令
    decrypt_parser = subparsers.add_parser('decrypt', help='解密单个值')
    decrypt_parser.add_argument('value', help='要解密的值（带 ENC: 前缀）')

    # encrypt-file 命令
    encrypt_file_parser = subparsers.add_parser('encrypt-file', help='加密 .env 文件')
    encrypt_file_parser.add_argument('path', help='.env 文件路径')
    encrypt_file_parser.add_argument('-o', '--output', help='输出文件路径')

    # decrypt-file 命令
    decrypt_file_parser = subparsers.add_parser('decrypt-file', help='解密 .env 文件')
    decrypt_file_parser.add_argument('path', help='.env 文件路径')
    decrypt_file_parser.add_argument('-o', '--output', help='输出文件路径')

    # generate-key 命令
    subparsers.add_parser('generate-key', help='生成新的加密密钥')

    # verify 命令
    subparsers.add_parser('verify', help='验证加密配置')

    args = parser.parse_args()

    if args.command == 'encrypt':
        result = encrypt_value(args.value)
        print(f"加密结果:\n{result}")

    elif args.command == 'decrypt':
        try:
            result = decrypt_value(args.value)
            print(f"解密结果:\n{result}")
        except Exception as e:
            print(f"解密失败: {e}")
            sys.exit(1)

    elif args.command == 'encrypt-file':
        print(f"加密文件: {args.path}")
        result = encrypt_env_file(args.path, args.output)
        print(f"\n完成！加密了 {result['encrypted']} 项配置")
        print(f"输出到: {result['output']}")

    elif args.command == 'decrypt-file':
        print(f"解密文件: {args.path}")
        result = decrypt_env_file(args.path, args.output)
        print(f"\n完成！解密了 {result['decrypted']} 项配置")
        print(f"输出到: {result['output']}")

    elif args.command == 'generate-key':
        key = generate_encryption_key()
        print(f"新密钥:\n{key}")
        print("\n请将此密钥保存到安全的地方，并设置为 ENCRYPTION_KEY 环境变量")

    elif args.command == 'verify':
        if verify_config():
            print("\n✓ 配置验证通过")
        else:
            print("\n✗ 配置验证失败")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
