"""
初始化更新日志数据
创建第一条系统更新日志
"""
import logging
from sqlalchemy.orm import Session
from datetime import datetime
from db.models.system import Changelog
from db.database import SessionLocal

logger = logging.getLogger(__name__)


# 更新日志数据
CHANGELOG_DATA = [
    {
        "version": "1.0.0",
        "title": "TalentMail 正式发布 🎉",
        "type": "release",
        "category": "feature",
        "is_major": True,
        "is_published": True,
        "author": "TalentMail Team",
        "tags": ["首发", "核心功能", "邮件系统"],
        "content": """### 🎯 核心功能

- **完整邮件系统**：发送、接收、转发、回复邮件
- **文件夹管理**：收件箱、发件箱、草稿箱、垃圾箱、已删除
- **邮件搜索**：支持按主题、发件人、内容搜索
- **邮件标签**：自定义标签分类管理

### 📧 邮件模板系统

- 系统邮件模板（验证码、欢迎邮件、密码重置）
- 支持 Markdown 格式
- 变量替换引擎
- 模板预览功能

### 🔐 安全功能

- 两步验证 (TOTP)
- 登录会话管理
- 密码强度检测
- 邮箱验证码

### 👥 用户管理

- 邀请码注册
- 用户角色权限
- 多套餐订阅
- 存储配额管理

### 📁 文件中转站

- 文件上传下载
- 分享链接生成
- 密码保护分享
- 过期时间设置

### 📬 临时邮箱

- 一键创建临时邮箱
- 自动接收邮件
- 支持查看邮件内容
- 统计分析""",
    },
    {
        "version": "1.1.0",
        "title": "可视化工作流引擎",
        "type": "release",
        "category": "feature",
        "is_major": True,
        "is_published": True,
        "author": "TalentMail Team",
        "tags": ["工作流", "自动化", "可视化编辑器"],
        "content": """### 🔄 工作流系统

- **可视化编辑器**：拖拽式节点编辑，所见即所得
- **节点类型**：触发器、条件判断、邮件操作、集成节点
- **连线逻辑**：支持条件分支、并行执行

### 📋 工作流模板

- 10+ 预置实用模板
- 重要邮件自动标星
- VIP 客户邮件提醒
- 垃圾邮件自动归档
- 休假自动回复
- 询盘自动回复
- 发票邮件归档

### 🎨 模板选择器

- 分类筛选
- 标签搜索
- 收藏功能
- 一键使用模板创建工作流

### ⚙️ 系统工作流

- 管理员可配置系统级工作流
- 用户注册验证流程
- 密码重置流程
- 邮件接收处理流程""",
    },
    {
        "version": "1.2.0",
        "title": "更新日志系统",
        "type": "release",
        "category": "feature",
        "is_major": False,
        "is_published": True,
        "author": "TalentMail Team",
        "tags": ["更新日志", "版本记录"],
        "content": """### 📝 更新日志

- 版本更新历史记录
- 支持 Markdown 格式
- 分类标签筛选
- 管理员发布管理

### 🔧 改进

- API 支持可选认证
- 前端组件优化
- 响应式布局适配""",
    },
]


def init_changelog_data(db: Session = None, force_update: bool = False):
    """
    初始化更新日志数据
    
    Args:
        db: 数据库会话，如果为 None 则创建新会话
        force_update: 是否强制更新已存在的记录
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True
    
    try:
        created_count = 0
        
        for data in CHANGELOG_DATA:
            version = data["version"]
            
            # 检查是否存在
            existing = db.query(Changelog).filter(
                Changelog.version == version
            ).first()
            
            if existing:
                if force_update:
                    for key, value in data.items():
                        setattr(existing, key, value)
                    existing.published_at = datetime.utcnow()
                    logger.info(f"更新更新日志: v{version}")
                else:
                    logger.debug(f"更新日志已存在，跳过: v{version}")
                continue
            
            # 创建新记录
            changelog = Changelog(
                **data,
                published_at=datetime.utcnow()
            )
            db.add(changelog)
            created_count += 1
            logger.info(f"创建更新日志: v{version}")
        
        db.commit()
        logger.info(f"更新日志初始化完成: 新增 {created_count} 条")
        
        return {"created": created_count}
        
    except Exception as e:
        db.rollback()
        logger.error(f"初始化更新日志失败: {e}")
        raise e
    finally:
        if should_close:
            db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_changelog_data()