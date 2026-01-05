"""
更新日志 Schema 定义
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChangelogBase(BaseModel):
    """更新日志基础字段"""
    version: str = Field(..., description="版本号，如 1.0.0, 1.1.0")
    title: str = Field(..., description="更新标题")
    content: str = Field(..., description="更新内容（支持Markdown格式）")
    type: str = Field(default="release", description="类型：release/hotfix/beta/alpha")
    category: Optional[str] = Field(None, description="分类：feature/bugfix/improvement/security")
    is_major: bool = Field(default=False, description="是否为重大更新")
    is_published: bool = Field(default=True, description="是否已发布")
    author: Optional[str] = Field(None, description="更新作者/负责人")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    breaking_changes: Optional[str] = Field(None, description="破坏性变更说明")
    migration_notes: Optional[str] = Field(None, description="迁移说明")


class ChangelogCreate(ChangelogBase):
    """创建更新日志"""
    pass


class ChangelogUpdate(BaseModel):
    """更新更新日志"""
    version: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    is_major: Optional[bool] = None
    is_published: Optional[bool] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    breaking_changes: Optional[str] = None
    migration_notes: Optional[str] = None


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