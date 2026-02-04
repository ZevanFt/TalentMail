"""add_email_fulltext_search

Revision ID: 2d0614e710cb
Revises: f542746d7be5
Create Date: 2026-02-02 16:04:12.703093

为邮件表添加 PostgreSQL 全文搜索支持：
1. 添加 search_vector 列（tsvector 类型）
2. 创建 GIN 索引加速搜索
3. 创建触发器自动更新 search_vector
4. 初始化现有数据的 search_vector
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2d0614e710cb'
down_revision: Union[str, Sequence[str], None] = 'f542746d7be5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加全文搜索支持"""

    # 1. 添加 search_vector 列（tsvector 类型）
    op.execute("""
        ALTER TABLE emails
        ADD COLUMN IF NOT EXISTS search_vector tsvector;
    """)

    # 2. 添加列注释
    op.execute("""
        COMMENT ON COLUMN emails.search_vector IS '全文搜索向量，包含主题、发件人和正文的分词结果';
    """)

    # 3. 创建 GIN 索引加速全文搜索
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_emails_search_vector
        ON emails USING GIN (search_vector);
    """)

    # 4. 创建更新 search_vector 的函数
    # 使用 'simple' 配置而不是语言特定配置，以更好地支持多语言内容
    op.execute("""
        CREATE OR REPLACE FUNCTION emails_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('simple', COALESCE(NEW.subject, '')), 'A') ||
                setweight(to_tsvector('simple', COALESCE(NEW.sender, '')), 'B') ||
                setweight(to_tsvector('simple', COALESCE(NEW.body_text, '')), 'C');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # 5. 创建触发器，在插入或更新时自动更新 search_vector
    op.execute("""
        DROP TRIGGER IF EXISTS emails_search_vector_trigger ON emails;
        CREATE TRIGGER emails_search_vector_trigger
        BEFORE INSERT OR UPDATE OF subject, sender, body_text
        ON emails
        FOR EACH ROW
        EXECUTE FUNCTION emails_search_vector_update();
    """)

    # 6. 为现有数据初始化 search_vector
    op.execute("""
        UPDATE emails SET search_vector =
            setweight(to_tsvector('simple', COALESCE(subject, '')), 'A') ||
            setweight(to_tsvector('simple', COALESCE(sender, '')), 'B') ||
            setweight(to_tsvector('simple', COALESCE(body_text, '')), 'C')
        WHERE search_vector IS NULL;
    """)


def downgrade() -> None:
    """移除全文搜索支持"""

    # 1. 删除触发器
    op.execute("DROP TRIGGER IF EXISTS emails_search_vector_trigger ON emails;")

    # 2. 删除函数
    op.execute("DROP FUNCTION IF EXISTS emails_search_vector_update();")

    # 3. 删除索引
    op.execute("DROP INDEX IF EXISTS idx_emails_search_vector;")

    # 4. 删除列
    op.execute("ALTER TABLE emails DROP COLUMN IF EXISTS search_vector;")
