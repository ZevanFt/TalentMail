"""encrypt external account passwords

Revision ID: encrypt_passwords_001
Revises:
Create Date: 2025-02-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'encrypt_passwords_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    加密现有的外部账户密码

    注意：这个迁移脚本需要手动运行，因为需要访问加密模块
    """
    # 创建一个临时的 Python 脚本来执行加密
    migration_script = """
import sys
sys.path.append('/app')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings
from core.crypto import encrypt_password
from db.models.external_account import ExternalAccount

# 创建数据库连接
engine = create_engine(settings.DATABASE_URL_DOCKER)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    # 获取所有外部账户
    accounts = db.query(ExternalAccount).all()

    for account in accounts:
        if account.password and not account.password.startswith('gAAAAA'):  # Fernet 加密的前缀
            # 加密密码
            encrypted_password = encrypt_password(account.password)
            account.password = encrypted_password
            print(f"已加密账户 {account.email} 的密码")

    # 提交更改
    db.commit()
    print(f"成功加密 {len(accounts)} 个账户的密码")

except Exception as e:
    db.rollback()
    print(f"迁移失败: {str(e)}")
    raise
finally:
    db.close()
"""

    # 将脚本写入临时文件并执行
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(migration_script)
        temp_file = f.name

    try:
        # 执行脚本
        os.system(f'cd /app && python {temp_file}')
    finally:
        # 清理临时文件
        os.unlink(temp_file)


def downgrade():
    """
    降级说明：由于安全原因，不支持将加密密码还原为明文
    """
    print("警告：出于安全考虑，不支持将加密密码降级为明文存储")
    print("如果需要降级，请手动处理密码字段")