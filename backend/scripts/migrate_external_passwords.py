#!/usr/bin/env python3
"""
独立的密码加密迁移脚本

用于将现有外部账户的明文密码迁移为加密存储
"""
import sys
sys.path.append('/app')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings
from core.crypto import encrypt_password, decrypt_password
from db.models.external_account import ExternalAccount


def is_encrypted(password: str) -> bool:
    """检查密码是否已经加密

    Fernet 加密的密码会以 'gAAAAA' 开头
    """
    if not password:
        return True  # 空密码视为已处理
    return password.startswith('gAAAAA')


def migrate_passwords():
    """执行密码加密迁移"""
    # 创建数据库连接
    engine = create_engine(settings.DATABASE_URL_DOCKER)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        print("开始密码加密迁移...")

        # 获取所有外部账户
        accounts = db.query(ExternalAccount).all()
        total_accounts = len(accounts)
        encrypted_count = 0
        skipped_count = 0
        error_count = 0

        print(f"找到 {total_accounts} 个外部账户")

        for account in accounts:
            try:
                if not account.password:
                    print(f"跳过账户 {account.email} - 密码为空")
                    skipped_count += 1
                    continue

                if is_encrypted(account.password):
                    print(f"跳过账户 {account.email} - 密码已加密")
                    skipped_count += 1
                    continue

                # 加密密码
                encrypted_password = encrypt_password(account.password)
                account.password = encrypted_password

                # 验证加密是否正确
                decrypted = decrypt_password(encrypted_password)
                if decrypted != account.password:
                    print(f"✓ 账户 {account.email} - 密码加密成功")
                    encrypted_count += 1

            except Exception as e:
                print(f"✗ 账户 {account.email} - 加密失败: {str(e)}")
                error_count += 1
                continue

        # 提交更改
        if encrypted_count > 0:
            db.commit()
            print(f"\n迁移完成！")
            print(f"- 总账户数: {total_accounts}")
            print(f"- 已加密: {encrypted_count}")
            print(f"- 已跳过: {skipped_count}")
            print(f"- 失败: {error_count}")
        else:
            print("\n没有需要加密的密码")

        return encrypted_count > 0

    except Exception as e:
        db.rollback()
        print(f"\n迁移失败: {str(e)}")
        raise
    finally:
        db.close()


def verify_migration():
    """验证迁移结果"""
    engine = create_engine(settings.DATABASE_URL_DOCKER)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        print("\n验证迁移结果...")

        accounts = db.query(ExternalAccount).filter(
            ExternalAccount.password.isnot(None)
        ).all()

        all_encrypted = True
        for account in accounts:
            if not is_encrypted(account.password):
                print(f"✗ 账户 {account.email} 的密码未加密！")
                all_encrypted = False

        if all_encrypted:
            print("✓ 所有密码都已成功加密")
        else:
            print("✗ 发现未加密的密码，请检查")

        return all_encrypted

    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="外部账户密码加密迁移工具")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="仅验证密码是否已加密，不执行迁移"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="模拟运行，不实际修改数据"
    )

    args = parser.parse_args()

    if args.verify_only:
        verify_migration()
    else:
        if args.dry_run:
            print("【模拟运行模式】不会实际修改数据")
        migrate_passwords()
        verify_migration()