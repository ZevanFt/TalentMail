"""
工作流模板 API 端点
提供工作流模板的 CRUD 和使用功能
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from pydantic import BaseModel
from datetime import datetime

from db.database import get_db
from api.deps import get_current_user, get_current_admin_user
from db.models.user import User
from db.models.workflow import (
    WorkflowTemplate, WorkflowTemplateTag, WorkflowTemplateFavorite,
    Workflow, WorkflowNode, WorkflowEdge
)

router = APIRouter()


# ==================== Schemas ====================

class TemplateTagCreate(BaseModel):
    tag: str


class WorkflowTemplateCreate(BaseModel):
    name: str
    name_en: Optional[str] = None
    description: Optional[str] = None
    description_en: Optional[str] = None
    category: str = "general"
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    default_config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class WorkflowTemplateUpdate(BaseModel):
    name: Optional[str] = None
    name_en: Optional[str] = None
    description: Optional[str] = None
    description_en: Optional[str] = None
    category: Optional[str] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    default_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    tags: Optional[List[str]] = None


class WorkflowTemplateResponse(BaseModel):
    id: int
    name: str
    name_en: Optional[str]
    description: Optional[str]
    description_en: Optional[str]
    category: str
    source_type: str
    author_id: Optional[int]
    author_name: Optional[str]
    nodes: List[Dict]
    edges: List[Dict]
    default_config: Optional[Dict]
    preview_image: Optional[str]
    thumbnail: Optional[str]
    use_count: int
    favorite_count: int
    review_status: str
    version: str
    is_active: bool
    is_featured: bool
    tags: List[str]
    is_favorited: bool = False
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class WorkflowTemplateListItem(BaseModel):
    id: int
    name: str
    name_en: Optional[str]
    description: Optional[str]
    category: str
    source_type: str
    author_name: Optional[str]
    preview_image: Optional[str]
    thumbnail: Optional[str]
    use_count: int
    favorite_count: int
    is_featured: bool
    tags: List[str]
    is_favorited: bool = False
    node_count: int
    
    class Config:
        from_attributes = True


class UseTemplateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


# ==================== 模板列表和详情 API ====================

@router.get("/", response_model=List[WorkflowTemplateListItem])
async def list_templates(
    category: Optional[str] = Query(None, description="分类过滤"),
    source_type: Optional[str] = Query(None, description="来源过滤: official/community/user"),
    tag: Optional[str] = Query(None, description="标签过滤"),
    q: Optional[str] = Query(None, description="搜索关键词"),
    featured_only: bool = Query(False, description="仅显示推荐"),
    favorites_only: bool = Query(False, description="仅显示收藏"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流模板列表"""
    query = db.query(WorkflowTemplate).filter(
        WorkflowTemplate.is_active == True,
        WorkflowTemplate.review_status == 'approved'
    )
    
    if category:
        query = query.filter(WorkflowTemplate.category == category)
    
    if source_type:
        query = query.filter(WorkflowTemplate.source_type == source_type)
    
    if featured_only:
        query = query.filter(WorkflowTemplate.is_featured == True)
    
    if q:
        search_pattern = f"%{q}%"
        query = query.filter(or_(
            WorkflowTemplate.name.ilike(search_pattern),
            WorkflowTemplate.name_en.ilike(search_pattern),
            WorkflowTemplate.description.ilike(search_pattern)
        ))
    
    if tag:
        query = query.join(WorkflowTemplateTag).filter(WorkflowTemplateTag.tag == tag)
    
    if favorites_only:
        query = query.join(WorkflowTemplateFavorite).filter(
            WorkflowTemplateFavorite.user_id == current_user.id
        )
    
    # 获取用户收藏的模板ID列表
    user_favorites = db.query(WorkflowTemplateFavorite.template_id).filter(
        WorkflowTemplateFavorite.user_id == current_user.id
    ).all()
    favorite_ids = {f.template_id for f in user_favorites}
    
    # 排序和分页
    query = query.order_by(
        WorkflowTemplate.is_featured.desc(),
        WorkflowTemplate.use_count.desc()
    )
    
    templates = query.offset((page - 1) * limit).limit(limit).all()
    
    # 构建响应
    result = []
    for t in templates:
        tags = [tag.tag for tag in t.tags]
        result.append(WorkflowTemplateListItem(
            id=t.id,
            name=t.name,
            name_en=t.name_en,
            description=t.description,
            category=t.category,
            source_type=t.source_type,
            author_name=t.author_name,
            preview_image=t.preview_image,
            thumbnail=t.thumbnail,
            use_count=t.use_count,
            favorite_count=t.favorite_count,
            is_featured=t.is_featured,
            tags=tags,
            is_favorited=t.id in favorite_ids,
            node_count=len(t.nodes) if t.nodes else 0
        ))
    
    return result


@router.get("/categories")
async def get_template_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有模板分类及其数量"""
    categories = db.query(
        WorkflowTemplate.category,
        func.count(WorkflowTemplate.id).label('count')
    ).filter(
        WorkflowTemplate.is_active == True,
        WorkflowTemplate.review_status == 'approved'
    ).group_by(WorkflowTemplate.category).all()
    
    category_labels = {
        'email': '邮件处理',
        'marketing': '营销推广',
        'notification': '通知提醒',
        'integration': '集成对接',
        'automation': '自动化',
        'general': '通用'
    }
    
    return [
        {
            'value': c.category,
            'label': category_labels.get(c.category, c.category),
            'count': c.count
        }
        for c in categories
    ]


@router.get("/tags")
async def get_template_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有标签及其使用次数"""
    tags = db.query(
        WorkflowTemplateTag.tag,
        func.count(WorkflowTemplateTag.id).label('count')
    ).join(WorkflowTemplate).filter(
        WorkflowTemplate.is_active == True,
        WorkflowTemplate.review_status == 'approved'
    ).group_by(WorkflowTemplateTag.tag).order_by(
        func.count(WorkflowTemplateTag.id).desc()
    ).limit(50).all()
    
    return [{'tag': t.tag, 'count': t.count} for t in tags]


@router.get("/{template_id}", response_model=WorkflowTemplateResponse)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模板详情"""
    template = db.query(WorkflowTemplate).filter(
        WorkflowTemplate.id == template_id,
        WorkflowTemplate.is_active == True
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # 检查用户是否收藏
    is_favorited = db.query(WorkflowTemplateFavorite).filter(
        WorkflowTemplateFavorite.user_id == current_user.id,
        WorkflowTemplateFavorite.template_id == template_id
    ).first() is not None
    
    tags = [tag.tag for tag in template.tags]
    
    return WorkflowTemplateResponse(
        id=template.id,
        name=template.name,
        name_en=template.name_en,
        description=template.description,
        description_en=template.description_en,
        category=template.category,
        source_type=template.source_type,
        author_id=template.author_id,
        author_name=template.author_name,
        nodes=template.nodes,
        edges=template.edges,
        default_config=template.default_config,
        preview_image=template.preview_image,
        thumbnail=template.thumbnail,
        use_count=template.use_count,
        favorite_count=template.favorite_count,
        review_status=template.review_status,
        version=template.version,
        is_active=template.is_active,
        is_featured=template.is_featured,
        tags=tags,
        is_favorited=is_favorited,
        created_at=template.created_at,
        updated_at=template.updated_at
    )


# ==================== 使用模板 API ====================

@router.post("/{template_id}/use")
async def use_template(
    template_id: int,
    data: UseTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """使用模板创建新工作流"""
    template = db.query(WorkflowTemplate).filter(
        WorkflowTemplate.id == template_id,
        WorkflowTemplate.is_active == True,
        WorkflowTemplate.review_status == 'approved'
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # 创建工作流
    workflow = Workflow(
        name=data.name or f"{template.name} (副本)",
        description=data.description or template.description,
        owner_id=current_user.id,
        scope='personal',
        category=template.category,
        status='draft',
        version=1
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    
    # 复制节点
    for node_data in template.nodes:
        node = WorkflowNode(
            workflow_id=workflow.id,
            node_id=node_data.get('node_id'),
            node_type=node_data.get('node_type'),
            node_subtype=node_data.get('node_subtype'),
            name=node_data.get('name'),
            position_x=node_data.get('position_x', 0),
            position_y=node_data.get('position_y', 0),
            config=node_data.get('config', {})
        )
        db.add(node)
    
    # 复制边
    for edge_data in template.edges:
        edge = WorkflowEdge(
            workflow_id=workflow.id,
            edge_id=edge_data.get('edge_id'),
            source_node_id=edge_data.get('source_node_id'),
            target_node_id=edge_data.get('target_node_id'),
            source_handle=edge_data.get('source_handle'),
            target_handle=edge_data.get('target_handle'),
            label=edge_data.get('label')
        )
        db.add(edge)
    
    # 更新使用计数
    template.use_count += 1
    
    db.commit()
    
    return {
        'success': True,
        'workflow_id': workflow.id,
        'message': f'已从模板 "{template.name}" 创建工作流'
    }


# ==================== 收藏 API ====================

@router.post("/{template_id}/favorite")
async def toggle_favorite(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """切换收藏状态"""
    template = db.query(WorkflowTemplate).filter(
        WorkflowTemplate.id == template_id,
        WorkflowTemplate.is_active == True
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    existing = db.query(WorkflowTemplateFavorite).filter(
        WorkflowTemplateFavorite.user_id == current_user.id,
        WorkflowTemplateFavorite.template_id == template_id
    ).first()
    
    if existing:
        db.delete(existing)
        template.favorite_count = max(0, template.favorite_count - 1)
        is_favorited = False
        message = '已取消收藏'
    else:
        favorite = WorkflowTemplateFavorite(
            user_id=current_user.id,
            template_id=template_id
        )
        db.add(favorite)
        template.favorite_count += 1
        is_favorited = True
        message = '已收藏'
    
    db.commit()
    
    return {
        'success': True,
        'is_favorited': is_favorited,
        'favorite_count': template.favorite_count,
        'message': message
    }


# ==================== 管理员 API ====================

@router.post("/", response_model=WorkflowTemplateResponse)
async def create_template(
    data: WorkflowTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """创建模板（管理员）"""
    template = WorkflowTemplate(
        name=data.name,
        name_en=data.name_en,
        description=data.description,
        description_en=data.description_en,
        category=data.category,
        source_type='official',
        author_id=current_user.id,
        author_name=current_user.display_name or current_user.email,
        nodes=data.nodes,
        edges=data.edges,
        default_config=data.default_config,
        review_status='approved',
        reviewed_at=datetime.utcnow(),
        reviewed_by=current_user.id
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    
    # 添加标签
    if data.tags:
        for tag_name in data.tags:
            tag = WorkflowTemplateTag(
                template_id=template.id,
                tag=tag_name.strip()
            )
            db.add(tag)
        db.commit()
    
    tags = [tag.tag for tag in template.tags]
    
    return WorkflowTemplateResponse(
        id=template.id,
        name=template.name,
        name_en=template.name_en,
        description=template.description,
        description_en=template.description_en,
        category=template.category,
        source_type=template.source_type,
        author_id=template.author_id,
        author_name=template.author_name,
        nodes=template.nodes,
        edges=template.edges,
        default_config=template.default_config,
        preview_image=template.preview_image,
        thumbnail=template.thumbnail,
        use_count=template.use_count,
        favorite_count=template.favorite_count,
        review_status=template.review_status,
        version=template.version,
        is_active=template.is_active,
        is_featured=template.is_featured,
        tags=tags,
        is_favorited=False,
        created_at=template.created_at,
        updated_at=template.updated_at
    )


@router.put("/{template_id}", response_model=WorkflowTemplateResponse)
async def update_template(
    template_id: int,
    data: WorkflowTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新模板（管理员）"""
    template = db.query(WorkflowTemplate).filter(
        WorkflowTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # 更新字段
    if data.name is not None:
        template.name = data.name
    if data.name_en is not None:
        template.name_en = data.name_en
    if data.description is not None:
        template.description = data.description
    if data.description_en is not None:
        template.description_en = data.description_en
    if data.category is not None:
        template.category = data.category
    if data.nodes is not None:
        template.nodes = data.nodes
    if data.edges is not None:
        template.edges = data.edges
    if data.default_config is not None:
        template.default_config = data.default_config
    if data.is_active is not None:
        template.is_active = data.is_active
    if data.is_featured is not None:
        template.is_featured = data.is_featured
    
    # 更新标签
    if data.tags is not None:
        # 删除旧标签
        db.query(WorkflowTemplateTag).filter(
            WorkflowTemplateTag.template_id == template_id
        ).delete()
        
        # 添加新标签
        for tag_name in data.tags:
            tag = WorkflowTemplateTag(
                template_id=template_id,
                tag=tag_name.strip()
            )
            db.add(tag)
    
    db.commit()
    db.refresh(template)
    
    tags = [tag.tag for tag in template.tags]
    
    is_favorited = db.query(WorkflowTemplateFavorite).filter(
        WorkflowTemplateFavorite.user_id == current_user.id,
        WorkflowTemplateFavorite.template_id == template_id
    ).first() is not None
    
    return WorkflowTemplateResponse(
        id=template.id,
        name=template.name,
        name_en=template.name_en,
        description=template.description,
        description_en=template.description_en,
        category=template.category,
        source_type=template.source_type,
        author_id=template.author_id,
        author_name=template.author_name,
        nodes=template.nodes,
        edges=template.edges,
        default_config=template.default_config,
        preview_image=template.preview_image,
        thumbnail=template.thumbnail,
        use_count=template.use_count,
        favorite_count=template.favorite_count,
        review_status=template.review_status,
        version=template.version,
        is_active=template.is_active,
        is_featured=template.is_featured,
        tags=tags,
        is_favorited=is_favorited,
        created_at=template.created_at,
        updated_at=template.updated_at
    )


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """删除模板（管理员）"""
    template = db.query(WorkflowTemplate).filter(
        WorkflowTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(template)
    db.commit()
    
    return {'success': True, 'message': '模板已删除'}


@router.get("/admin/pending", response_model=List[WorkflowTemplateListItem])
async def list_pending_templates(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取待审核模板列表（管理员）"""
    query = db.query(WorkflowTemplate).filter(
        WorkflowTemplate.review_status == 'pending'
    )
    
    templates = query.order_by(
        WorkflowTemplate.created_at.desc()
    ).offset((page - 1) * limit).limit(limit).all()
    
    result = []
    for t in templates:
        tags = [tag.tag for tag in t.tags]
        result.append(WorkflowTemplateListItem(
            id=t.id,
            name=t.name,
            name_en=t.name_en,
            description=t.description,
            category=t.category,
            source_type=t.source_type,
            author_name=t.author_name,
            preview_image=t.preview_image,
            thumbnail=t.thumbnail,
            use_count=t.use_count,
            favorite_count=t.favorite_count,
            is_featured=t.is_featured,
            tags=tags,
            is_favorited=False,
            node_count=len(t.nodes) if t.nodes else 0
        ))
    
    return result


@router.post("/{template_id}/review")
async def review_template(
    template_id: int,
    action: str = Query(..., description="操作: approve/reject"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """审核模板（管理员）"""
    template = db.query(WorkflowTemplate).filter(
        WorkflowTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if action == 'approve':
        template.review_status = 'approved'
        message = '模板已通过审核'
    elif action == 'reject':
        template.review_status = 'rejected'
        message = '模板已拒绝'
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    template.reviewed_at = datetime.utcnow()
    template.reviewed_by = current_user.id
    
    db.commit()
    
    return {'success': True, 'message': message}