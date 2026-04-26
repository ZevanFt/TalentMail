"""
更新日志 Schema 定义
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChangelogBase(BaseModel):
    """更新日志基础字段"""
    version: str = Field(..., max_length=50, description="版本号，如 1.0.0, 1.1.0")
    title: str = Field(..., max_length=255, description="更新标题")
    content: str = Field(..., max_length=100_000, description="更新内容（支持Markdown格式）")
    type: str = Field(default="release", max_length=20, description="类型：release/hotfix/beta/alpha")
    category: Optional[str] = Field(None, max_length=30, description="分类：feature/bugfix/improvement/security")
    is_major: bool = Field(default=False, description="是否为重大更新")
    is_published: bool = Field(default=True, description="是否已发布")
    author: Optional[str] = Field(None, max_length=100, description="更新作者/负责人")
    tags: Optional[List[str]] = Field(None, max_length=20, description="标签列表")
    breaking_changes: Optional[str] = Field(None, max_length=50_000, description="破坏性变更说明")
    migration_notes: Optional[str] = Field(None, max_length=50_000, description="迁移说明")


class ChangelogCreate(ChangelogBase):
    """创建更新日志"""
    pass


class ChangelogUpdate(BaseModel):
    """更新更新日志"""
    version: Optional[str] = Field(default=None, max_length=50)
    title: Optional[str] = Field(default=None, max_length=255)
    content: Optional[str] = Field(default=None, max_length=100_000)
    type: Optional[str] = Field(default=None, max_length=20)
    category: Optional[str] = Field(default=None, max_length=30)
    is_major: Optional[bool] = None
    is_published: Optional[bool] = None
    author: Optional[str] = Field(default=None, max_length=100)
    tags: Optional[List[str]] = Field(default=None, max_length=20)
    breaking_changes: Optional[str] = Field(default=None, max_length=50_000)
    migration_notes: Optional[str] = Field(default=None, max_length=50_000)


class ChangelogResponse(ChangelogBase):
    """更新日志响应"""
    id: int
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ChangelogListResponse(BaseModel):
    """更新日志列表响应"""
    items: List[ChangelogResponse]
    total: int
    page: int
    page_size: int
    has_more: bool