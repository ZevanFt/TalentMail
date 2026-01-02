"""模板元数据、全局变量和触发器模型"""
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import relationship
from ..database import Base


class TemplateMetadata(Base):
    """模板元数据定义表 - 定义系统支持的所有模板类型及其变量"""
    __tablename__ = "template_metadata"
    __table_args__ = {'comment': '模板元数据定义表，定义系统支持的所有模板类型及其变量'}
    
    id = Column(Integer, primary_key=True, comment="元数据唯一标识符")
    code = Column(String(50), unique=True, nullable=False, index=True, comment="模板代码，与 system_email_templates.code 对应")
    name = Column(String(100), nullable=False, comment="显示名称")
    category = Column(String(50), nullable=False, comment="业务分类: auth/notification/collaboration")
    description = Column(Text, nullable=True, comment="详细描述")
    trigger_description = Column(Text, nullable=True, comment="触发时机说明")
    variables = Column(JSON, nullable=False, default=list, comment="变量定义列表")
    default_subject = Column(String(255), nullable=True, comment="默认主题")
    default_body_html = Column(Text, nullable=True, comment="默认 HTML 内容")
    default_body_text = Column(Text, nullable=True, comment="默认纯文本内容")
    is_system = Column(Boolean, default=True, comment="是否系统内置（内置不可删除）")
    sort_order = Column(Integer, default=0, comment="排序")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")


class GlobalVariable(Base):
    """全局变量表 - 所有模板都可以使用的变量"""
    __tablename__ = "global_variables"
    __table_args__ = {'comment': '全局变量表，所有模板都可以使用的变量'}
    
    id = Column(Integer, primary_key=True, comment="变量唯一标识符")
    key = Column(String(50), unique=True, nullable=False, index=True, comment="变量名")
    label = Column(String(100), nullable=False, comment="显示名称")
    value = Column(Text, nullable=False, default="", comment="变量值（可以是静态值或表达式）")
    value_type = Column(String(20), default="static", comment="值类型: static/dynamic/config")
    description = Column(String(255), nullable=True, comment="说明")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")