"""
模板渲染引擎 - 阶段一核心组件，阶段二复用
负责处理模板变量替换、全局变量注入等
"""
import re
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from db.models.template import GlobalVariable
from db.models.system import SystemEmailTemplate
from core.config import settings


class TemplateEngine:
    def __init__(self, db: Session):
        self.db = db
        self._global_vars_cache = None

    def get_global_variables(self) -> Dict[str, Any]:
        """获取全局变量"""
        if self._global_vars_cache is not None:
            return self._global_vars_cache

        # 从数据库获取
        db_vars = self.db.query(GlobalVariable).filter(
            GlobalVariable.is_active == True
        ).all()
        
        variables = {}
        for var in db_vars:
            if var.value_type == 'config':
                # 从配置读取
                if var.key == 'app_name':
                    variables[var.key] = settings.APP_NAME
                elif var.key == 'site_url':
                    # 使用 DOMAIN 构建网站 URL
                    variables[var.key] = f"https://{settings.DOMAIN}"
                elif var.key == 'support_email':
                    variables[var.key] = f"support@{settings.BASE_DOMAIN}"
                elif var.key == 'company_name':
                    variables[var.key] = getattr(settings, 'COMPANY_NAME', settings.APP_NAME)
                else:
                    variables[var.key] = var.value
            elif var.value_type == 'dynamic':
                # 动态计算
                if var.key == 'current_year':
                    variables[var.key] = str(datetime.now().year)
                elif var.key == 'current_date':
                    variables[var.key] = datetime.now().strftime('%Y-%m-%d')
                else:
                    variables[var.key] = var.value
            else:
                # 静态值
                variables[var.key] = var.value
        
        self._global_vars_cache = variables
        return variables

    def render(self, template_str: str, context: Dict[str, Any]) -> str:
        """
        渲染模板字符串
        支持 {{variable}} 格式
        支持 {{variable|default:"value"}} 格式
        支持 {{#if variable}}...{{/if}} 条件语法
        """
        if not template_str:
            return ""

        # 获取全局变量并合并上下文
        global_vars = self.get_global_variables()
        full_context = {**global_vars, **context}
        
        result = template_str
        
        # 1. 首先处理条件语法 {{#if variable}}...{{/if}}
        result = self._process_conditionals(result, full_context)
        
        # 2. 然后处理变量替换 {{variable}} 和 {{variable|default:"value"}}
        result = self._process_variables(result, full_context)
            
        return result
    
    def _process_conditionals(self, template_str: str, context: Dict[str, Any]) -> str:
        """
        处理条件语法 {{#if variable}}...{{/if}}
        支持嵌套条件
        """
        # 使用非贪婪匹配处理条件块
        # 匹配 {{#if var}}...{{/if}}，支持多行
        pattern = r'\{\{#if\s+(\w+)\}\}(.*?)\{\{/if\}\}'
        
        def replace_conditional(match):
            var_name = match.group(1)
            content = match.group(2)
            
            # 检查变量是否存在且为真值
            value = context.get(var_name)
            
            # 判断真值：非空字符串、非零数字、非空列表等
            is_truthy = bool(value) and value not in ['', '0', 'false', 'False', 'null', 'None']
            
            if is_truthy:
                # 递归处理嵌套条件
                return self._process_conditionals(content, context)
            else:
                return ''
        
        # 使用 re.DOTALL 让 . 匹配换行符
        result = re.sub(pattern, replace_conditional, template_str, flags=re.DOTALL)
        
        return result
    
    def _process_variables(self, template_str: str, context: Dict[str, Any]) -> str:
        """
        处理变量替换 {{variable}} 和 {{variable|default:"value"}}
        """
        result = template_str
        
        # 查找所有 {{...}} 模式（排除条件语法）
        matches = list(re.finditer(r'\{\{([^#/][^}]*?)\}\}', template_str))
        
        for match in matches:
            full_match = match.group(0)
            content = match.group(1).strip()
            
            # 跳过空内容
            if not content:
                continue
            
            # 处理默认值过滤器 |default:"..."
            default_value = None
            if '|default:' in content:
                parts = content.split('|default:')
                var_name = parts[0].strip()
                # 提取引号中的默认值
                default_match = re.search(r'["\'](.+?)["\']', parts[1])
                if default_match:
                    default_value = default_match.group(1)
            else:
                var_name = content
            
            # 获取变量值
            value = context.get(var_name)
            
            # 如果变量不存在或为空，使用默认值
            if value is None or value == '':
                if default_value is not None:
                    value = default_value
                else:
                    # 变量未找到且无默认值，替换为空字符串（更干净的输出）
                    value = ''
            
            result = result.replace(full_match, str(value), 1)
            
        return result

    def render_template(self, template_code: str, context: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        渲染完整模板，返回 subject, body_html, body_text
        """
        template = self.db.query(SystemEmailTemplate).filter(
            SystemEmailTemplate.code == template_code,
            SystemEmailTemplate.is_active == True
        ).first()
        
        if not template:
            return None
            
        return {
            "subject": self.render(template.subject, context),
            "body_html": self.render(template.body_html, context),
            "body_text": self.render(template.body_text or "", context)
        }