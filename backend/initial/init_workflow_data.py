"""
初始化工作流相关数据
包括节点类型、系统工作流定义
"""
import json
from sqlalchemy.orm import Session


def init_node_types(db: Session, force_update_icons: bool = True):
    """初始化节点类型数据
    
    Args:
        db: 数据库会话
        force_update_icons: 如果为 True，即使数据存在也会更新图标
    """
    from db.models.workflow import NodeType
    
    # 检查是否已存在
    existing_count = db.query(NodeType).count()
    
    node_types = [
        # ==================== 触发器节点 ====================
        {
            "code": "trigger_email_received",
            "name": "收到邮件",
            "name_en": "Email Received",
            "category": "trigger",
            "icon": "Mail",
            "color": "#10b981",
            "description": "当收到新邮件时触发",
            "config_schema": {
                "type": "object",
                "properties": {
                    "filter_sender": {"type": "string", "title": "发件人过滤"},
                    "filter_subject": {"type": "string", "title": "主题过滤"},
                    "filter_folder": {"type": "string", "title": "文件夹过滤"}
                }
            },
            "output_variables": ["sender_email", "sender_name", "subject", "body_text", "received_time"]
        },
        {
            "code": "trigger_user_event",
            "name": "用户事件",
            "name_en": "User Event",
            "category": "trigger",
            "icon": "User",
            "color": "#10b981",
            "description": "当用户事件发生时触发",
            "config_schema": {
                "type": "object",
                "properties": {
                    "event_type": {
                        "type": "string",
                        "title": "事件类型",
                        "enum": ["user.registered", "user.login", "user.login_new_device", "user.password_changed"],
                        "enumNames": ["用户注册", "用户登录", "新设备登录", "密码修改"]
                    }
                },
                "required": ["event_type"]
            },
            "output_variables": ["user_id", "user_email", "user_name", "event_time"]
        },
        {
            "code": "trigger_scheduled",
            "name": "定时触发",
            "name_en": "Scheduled",
            "category": "trigger",
            "icon": "Clock",
            "color": "#10b981",
            "description": "按照设定的时间表触发",
            "config_schema": {
                "type": "object",
                "properties": {
                    "cron": {"type": "string", "title": "Cron 表达式", "description": "例如: 0 9 * * * (每天9点)"},
                    "timezone": {"type": "string", "title": "时区", "default": "Asia/Shanghai"}
                },
                "required": ["cron"]
            }
        },
        {
            "code": "trigger_webhook",
            "name": "Webhook 触发",
            "name_en": "Webhook",
            "category": "trigger",
            "icon": "Link",
            "color": "#10b981",
            "description": "通过 Webhook 调用触发",
            "config_schema": {
                "type": "object",
                "properties": {
                    "secret": {"type": "string", "title": "验证密钥"},
                    "method": {"type": "string", "enum": ["GET", "POST"], "default": "POST"}
                }
            }
        },
        {
            "code": "trigger_manual",
            "name": "手动触发",
            "name_en": "Manual",
            "category": "trigger",
            "icon": "MousePointer",
            "color": "#10b981",
            "description": "手动触发执行"
        },
        {
            "code": "trigger_form_submit",
            "name": "表单提交",
            "name_en": "Form Submit",
            "category": "trigger",
            "icon": "FileText",
            "color": "#10b981",
            "description": "当表单提交时触发（如注册表单）",
            "output_variables": ["form_data"]
        },
        
        # ==================== 逻辑节点 ====================
        {
            "code": "logic_condition",
            "name": "条件分支",
            "name_en": "Condition",
            "category": "logic",
            "icon": "GitBranch",
            "color": "#3b82f6",
            "description": "根据条件判断走不同分支",
            "output_ports": [
                {"id": "true", "label": "是"},
                {"id": "false", "label": "否"}
            ],
            "config_schema": {
                "type": "object",
                "properties": {
                    "conditions": {
                        "type": "array",
                        "title": "条件列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "field": {"type": "string"},
                                "operator": {
                                    "type": "string",
                                    "enum": ["equals", "not_equals", "contains", "not_contains",
                                             "starts_with", "ends_with", "is_empty", "is_not_empty",
                                             "greater_than", "less_than", "matches_regex"]
                                },
                                "value": {"type": "string"}
                            }
                        }
                    },
                    "logic": {"type": "string", "enum": ["and", "or"], "default": "and"}
                }
            }
        },
        {
            "code": "logic_switch",
            "name": "多条件分支",
            "name_en": "Switch",
            "category": "logic",
            "icon": "ListFilter",
            "color": "#3b82f6",
            "description": "根据多个条件走不同分支",
            "config_schema": {
                "type": "object",
                "properties": {
                    "branches": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "conditions": {"type": "array"}
                            }
                        }
                    },
                    "default_branch": {"type": "string", "title": "默认分支"}
                }
            }
        },
        {
            "code": "logic_delay",
            "name": "延迟执行",
            "name_en": "Delay",
            "category": "logic",
            "icon": "Timer",
            "color": "#3b82f6",
            "description": "延迟一段时间后继续执行",
            "config_schema": {
                "type": "object",
                "properties": {
                    "delay_value": {"type": "integer", "title": "延迟时间", "default": 5},
                    "delay_unit": {
                        "type": "string",
                        "title": "时间单位",
                        "enum": ["seconds", "minutes", "hours", "days"],
                        "enumNames": ["秒", "分钟", "小时", "天"],
                        "default": "minutes"
                    }
                }
            }
        },
        {
            "code": "logic_parallel",
            "name": "并行执行",
            "name_en": "Parallel",
            "category": "logic",
            "icon": "GitMerge",
            "color": "#3b82f6",
            "description": "同时执行多个分支"
        },
        {
            "code": "logic_wait",
            "name": "等待输入",
            "name_en": "Wait for Input",
            "category": "logic",
            "icon": "Pause",
            "color": "#3b82f6",
            "description": "等待用户输入或外部事件",
            "config_schema": {
                "type": "object",
                "properties": {
                    "wait_type": {
                        "type": "string",
                        "enum": ["user_input", "verification_code", "approval"],
                        "enumNames": ["用户输入", "验证码", "审批"]
                    },
                    "timeout_minutes": {"type": "integer", "title": "超时时间(分钟)", "default": 15}
                }
            }
        },
        
        # ==================== 邮件动作节点 ====================
        {
            "code": "action_send_email",
            "name": "发送邮件",
            "name_en": "Send Email",
            "category": "email_action",
            "icon": "Send",
            "color": "#f59e0b",
            "description": "发送一封邮件",
            "config_schema": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "title": "收件人"},
                    "cc": {"type": "string", "title": "抄送"},
                    "subject": {"type": "string", "title": "主题"},
                    "body": {"type": "string", "title": "正文", "format": "html"}
                },
                "required": ["to", "subject", "body"]
            }
        },
        {
            "code": "action_send_template",
            "name": "发送模板邮件",
            "name_en": "Send Template Email",
            "category": "email_action",
            "icon": "FileCode",
            "color": "#f59e0b",
            "description": "使用预设模板发送邮件",
            "config_schema": {
                "type": "object",
                "properties": {
                    "template_code": {"type": "string", "title": "邮件模板"},
                    "to_type": {
                        "type": "string",
                        "title": "发送给",
                        "enum": ["trigger_user", "form_field", "fixed_email", "admin"],
                        "enumNames": ["触发用户", "表单字段", "指定邮箱", "管理员"],
                        "default": "trigger_user"
                    },
                    "to_field": {"type": "string", "title": "邮箱字段名"},
                    "to_email": {"type": "string", "title": "收件人邮箱"},
                    "variables": {"type": "object", "title": "变量覆盖"}
                },
                "required": ["template_code", "to_type"]
            }
        },
        {
            "code": "action_reply",
            "name": "回复邮件",
            "name_en": "Reply Email",
            "category": "email_action",
            "icon": "Reply",
            "color": "#f59e0b",
            "description": "回复触发的邮件",
            "config_schema": {
                "type": "object",
                "properties": {
                    "body": {"type": "string", "title": "回复内容", "format": "html"},
                    "template_code": {"type": "string", "title": "使用模板"}
                }
            }
        },
        {
            "code": "action_forward",
            "name": "转发邮件",
            "name_en": "Forward Email",
            "category": "email_action",
            "icon": "Forward",
            "color": "#f59e0b",
            "description": "转发触发的邮件",
            "config_schema": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "title": "转发给"},
                    "add_note": {"type": "string", "title": "添加备注"}
                },
                "required": ["to"]
            }
        },
        
        # ==================== 邮件处理节点 ====================
        {
            "code": "operation_move_folder",
            "name": "移动到文件夹",
            "name_en": "Move to Folder",
            "category": "email_operation",
            "icon": "FolderInput",
            "color": "#8b5cf6",
            "description": "将邮件移动到指定文件夹",
            "config_schema": {
                "type": "object",
                "properties": {
                    "folder": {"type": "string", "title": "目标文件夹"}
                },
                "required": ["folder"]
            }
        },
        {
            "code": "operation_add_tag",
            "name": "添加标签",
            "name_en": "Add Tag",
            "category": "email_operation",
            "icon": "Tag",
            "color": "#8b5cf6",
            "description": "为邮件添加标签",
            "config_schema": {
                "type": "object",
                "properties": {
                    "tag": {"type": "string", "title": "标签名"},
                    "color": {"type": "string", "title": "标签颜色"}
                },
                "required": ["tag"]
            }
        },
        {
            "code": "operation_remove_tag",
            "name": "移除标签",
            "name_en": "Remove Tag",
            "category": "email_operation",
            "icon": "TagOff",
            "color": "#8b5cf6",
            "description": "移除邮件的标签",
            "config_schema": {
                "type": "object",
                "properties": {
                    "tag": {"type": "string", "title": "标签名"}
                },
                "required": ["tag"]
            }
        },
        {
            "code": "operation_mark_starred",
            "name": "标记星标",
            "name_en": "Mark Starred",
            "category": "email_operation",
            "icon": "Star",
            "color": "#8b5cf6",
            "description": "标记邮件为星标"
        },
        {
            "code": "operation_mark_read",
            "name": "标记已读",
            "name_en": "Mark Read",
            "category": "email_operation",
            "icon": "CheckCircle",
            "color": "#8b5cf6",
            "description": "标记邮件为已读"
        },
        {
            "code": "operation_delete",
            "name": "删除邮件",
            "name_en": "Delete Email",
            "category": "email_operation",
            "icon": "Trash2",
            "color": "#8b5cf6",
            "description": "删除邮件（移到垃圾箱）"
        },
        {
            "code": "operation_archive",
            "name": "归档邮件",
            "name_en": "Archive Email",
            "category": "email_operation",
            "icon": "Archive",
            "color": "#8b5cf6",
            "description": "归档邮件"
        },
        
        # ==================== 数据处理节点 ====================
        {
            "code": "data_validate",
            "name": "数据验证",
            "name_en": "Validate Data",
            "category": "data",
            "icon": "ShieldCheck",
            "color": "#06b6d4",
            "description": "验证数据格式和内容",
            "config_schema": {
                "type": "object",
                "properties": {
                    "validations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "field": {"type": "string"},
                                "rules": {"type": "array"}
                            }
                        }
                    }
                }
            }
        },
        {
            "code": "data_generate_code",
            "name": "生成验证码",
            "name_en": "Generate Code",
            "category": "data",
            "icon": "Hash",
            "color": "#06b6d4",
            "description": "生成验证码",
            "config_schema": {
                "type": "object",
                "properties": {
                    "length": {"type": "integer", "title": "长度", "default": 6},
                    "type": {
                        "type": "string",
                        "enum": ["numeric", "alphanumeric"],
                        "enumNames": ["纯数字", "字母+数字"],
                        "default": "numeric"
                    },
                    "expire_minutes": {"type": "integer", "title": "有效期(分钟)", "default": 15}
                }
            },
            "output_variables": ["generated_code", "expire_time"]
        },
        {
            "code": "data_create_user",
            "name": "创建用户",
            "name_en": "Create User",
            "category": "data",
            "icon": "UserPlus",
            "color": "#06b6d4",
            "description": "创建新用户账户",
            "config_schema": {
                "type": "object",
                "properties": {
                    "email_field": {"type": "string", "title": "邮箱字段"},
                    "password_field": {"type": "string", "title": "密码字段"},
                    "display_name_field": {"type": "string", "title": "显示名称字段"}
                }
            },
            "output_variables": ["user_id", "user_email"]
        },
        {
            "code": "data_update_user",
            "name": "更新用户",
            "name_en": "Update User",
            "category": "data",
            "icon": "UserCog",
            "color": "#06b6d4",
            "description": "更新用户信息"
        },
        {
            "code": "data_verify_code",
            "name": "验证码校验",
            "name_en": "Verify Code",
            "category": "data",
            "icon": "KeyRound",
            "color": "#06b6d4",
            "description": "校验用户输入的验证码",
            "output_ports": [
                {"id": "valid", "label": "验证通过"},
                {"id": "invalid", "label": "验证失败"}
            ]
        },
        {
            "code": "data_verify_password",
            "name": "密码校验",
            "name_en": "Verify Password",
            "category": "data",
            "icon": "Lock",
            "color": "#06b6d4",
            "description": "校验用户密码",
            "output_ports": [
                {"id": "valid", "label": "验证通过"},
                {"id": "invalid", "label": "验证失败"}
            ]
        },
        
        # ==================== 集成节点 ====================
        {
            "code": "integration_webhook",
            "name": "Webhook 调用",
            "name_en": "Call Webhook",
            "category": "integration",
            "icon": "Globe",
            "color": "#ec4899",
            "description": "调用外部 Webhook",
            "config_schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "title": "URL"},
                    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"], "default": "POST"},
                    "headers": {"type": "object", "title": "请求头"},
                    "body": {"type": "object", "title": "请求体"}
                },
                "required": ["url", "method"]
            }
        },
        {
            "code": "integration_log",
            "name": "记录日志",
            "name_en": "Log Message",
            "category": "integration",
            "icon": "ScrollText",
            "color": "#ec4899",
            "description": "记录日志信息",
            "config_schema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "title": "日志内容"},
                    "level": {"type": "string", "enum": ["info", "warning", "error"], "default": "info"}
                }
            }
        },
        {
            "code": "integration_trigger_workflow",
            "name": "触发其他工作流",
            "name_en": "Trigger Workflow",
            "category": "integration",
            "icon": "Zap",
            "color": "#ec4899",
            "description": "触发另一个工作流",
            "config_schema": {
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "integer", "title": "目标工作流"},
                    "pass_data": {"type": "boolean", "title": "传递当前数据", "default": True}
                }
            }
        },
        {
            "code": "integration_notify",
            "name": "发送通知",
            "name_en": "Send Notification",
            "category": "integration",
            "icon": "Bell",
            "color": "#ec4899",
            "description": "发送系统通知",
            "config_schema": {
                "type": "object",
                "properties": {
                    "notify_type": {
                        "type": "string",
                        "enum": ["websocket", "email", "both"],
                        "enumNames": ["实时推送", "邮件", "两者都"]
                    },
                    "message": {"type": "string", "title": "通知内容"}
                }
            }
        },
        
        # ==================== 结束节点 ====================
        {
            "code": "end_success",
            "name": "成功结束",
            "name_en": "Success",
            "category": "end",
            "icon": "CircleCheck",
            "color": "#22c55e",
            "description": "流程成功结束",
            "config_schema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "title": "成功消息"},
                    "return_data": {"type": "object", "title": "返回数据"}
                }
            }
        },
        {
            "code": "end_failure",
            "name": "失败结束",
            "name_en": "Failure",
            "category": "end",
            "icon": "CircleX",
            "color": "#ef4444",
            "description": "流程失败结束",
            "config_schema": {
                "type": "object",
                "properties": {
                    "error_code": {"type": "string", "title": "错误代码"},
                    "error_message": {"type": "string", "title": "错误信息"}
                }
            }
        },
    ]
    
    if existing_count > 0 and force_update_icons:
        # 更新现有节点类型的图标
        updated_count = 0
        for data in node_types:
            existing_node = db.query(NodeType).filter(NodeType.code == data["code"]).first()
            if existing_node:
                new_icon = data.get("icon")
                if existing_node.icon != new_icon:
                    existing_node.icon = new_icon
                    existing_node.color = data.get("color")  # 同时更新颜色
                    updated_count += 1
        db.commit()
        print(f"更新了 {updated_count} 个节点类型的图标")
        return
    
    if existing_count > 0:
        print("节点类型数据已存在，跳过初始化")
        return
    
    for data in node_types:
        node_type = NodeType(
            code=data["code"],
            name=data["name"],
            name_en=data.get("name_en"),
            category=data["category"],
            icon=data.get("icon"),
            color=data.get("color"),
            description=data.get("description"),
            input_ports=data.get("input_ports", []),
            output_ports=data.get("output_ports", []),
            config_schema=data.get("config_schema"),
            available_variables=data.get("available_variables"),
            output_variables=data.get("output_variables"),
            is_active=True,
            is_system=True,
            sort_order=node_types.index(data)
        )
        db.add(node_type)
    
    db.commit()
    print(f"成功初始化 {len(node_types)} 个节点类型")


def init_system_workflows(db: Session):
    """初始化系统工作流数据"""
    from db.models.workflow import SystemWorkflow
    
    # 检查是否已存在
    # existing = db.query(SystemWorkflow).first()
    # if existing:
    #     print("系统工作流数据已存在，跳过初始化")
    #     return
    
    system_workflows = [
        {
            "code": "user_registration",
            "name": "用户注册流程",
            "name_en": "User Registration",
            "description": "处理用户注册的完整流程，包括验证码发送、账户创建、欢迎邮件等",
            "category": "auth",
            "nodes": [
                {
                    "node_id": "trigger_1",
                    "node_type": "trigger",
                    "node_subtype": "trigger_form_submit",
                    "name": "提交注册表单",
                    "position_x": 250,
                    "position_y": 50,
                    "is_system": True,
                    "is_required": True,
                    "can_configure": False
                },
                {
                    "node_id": "validate_1",
                    "node_type": "data",
                    "node_subtype": "data_validate",
                    "name": "验证表单数据",
                    "position_x": 250,
                    "position_y": 150,
                    "config": {
                        "validations": [
                            {"field": "email", "rules": ["required", "email"]},
                            {"field": "password", "rules": ["required", "min:8"]}
                        ]
                    },
                    "is_system": True,
                    "is_required": True
                },
                {
                    "node_id": "condition_verification",
                    "node_type": "logic",
                    "node_subtype": "logic_condition",
                    "name": "需要验证码？",
                    "position_x": 250,
                    "position_y": 250,
                    "config": {
                        "conditions": [{"field": "config.require_verification", "operator": "equals", "value": True}]
                    }
                },
                {
                    "node_id": "generate_code",
                    "node_type": "data",
                    "node_subtype": "data_generate_code",
                    "name": "生成验证码",
                    "position_x": 100,
                    "position_y": 350,
                    "config": {
                        "length": 6,
                        "type": "numeric",
                        "expire_minutes": 15
                    }
                },
                {
                    "node_id": "send_verification",
                    "node_type": "action",
                    "node_subtype": "action_send_template",
                    "name": "发送验证码邮件",
                    "position_x": 100,
                    "position_y": 450,
                    "config": {
                        "template_code": "verification_code_register",
                        "to_type": "form_field",
                        "to_field": "email"
                    },
                    "can_configure": True
                },
                {
                    "node_id": "wait_verify",
                    "node_type": "logic",
                    "node_subtype": "logic_wait",
                    "name": "等待用户验证",
                    "position_x": 100,
                    "position_y": 550,
                    "config": {
                        "wait_type": "verification_code",
                        "timeout_minutes": 15
                    }
                },
                {
                    "node_id": "verify_code",
                    "node_type": "data",
                    "node_subtype": "data_verify_code",
                    "name": "校验验证码",
                    "position_x": 100,
                    "position_y": 650,
                    "is_system": True
                },
                {
                    "node_id": "create_user",
                    "node_type": "data",
                    "node_subtype": "data_create_user",
                    "name": "创建账户",
                    "position_x": 250,
                    "position_y": 750,
                    "is_system": True,
                    "is_required": True
                },
                {
                    "node_id": "condition_welcome",
                    "node_type": "logic",
                    "node_subtype": "logic_condition",
                    "name": "发送欢迎邮件？",
                    "position_x": 250,
                    "position_y": 850,
                    "config": {
                        "conditions": [{"field": "config.send_welcome_email", "operator": "equals", "value": True}]
                    }
                },
                {
                    "node_id": "send_welcome",
                    "node_type": "action",
                    "node_subtype": "action_send_template",
                    "name": "发送欢迎邮件",
                    "position_x": 100,
                    "position_y": 950,
                    "config": {
                        "template_code": "welcome_email",
                        "to_type": "trigger_user"
                    },
                    "can_configure": True
                },
                {
                    "node_id": "condition_notify_admin",
                    "node_type": "logic",
                    "node_subtype": "logic_condition",
                    "name": "通知管理员？",
                    "position_x": 250,
                    "position_y": 1050,
                    "config": {
                        "conditions": [{"field": "config.notify_admin", "operator": "equals", "value": True}]
                    }
                },
                {
                    "node_id": "notify_admin",
                    "node_type": "action",
                    "node_subtype": "action_send_template",
                    "name": "通知管理员",
                    "position_x": 100,
                    "position_y": 1150,
                    "config": {
                        "template_code": "admin_new_user_notification",
                        "to_type": "admin"
                    },
                    "can_configure": True
                },
                {
                    "node_id": "end_success",
                    "node_type": "end",
                    "node_subtype": "end_success",
                    "name": "注册成功",
                    "position_x": 250,
                    "position_y": 1250,
                    "config": {
                        "message": "注册成功"
                    }
                },
                {
                    "node_id": "end_failed",
                    "node_type": "end",
                    "node_subtype": "end_failure",
                    "name": "验证失败",
                    "position_x": 400,
                    "position_y": 750,
                    "config": {
                        "error_code": "VERIFICATION_FAILED",
                        "error_message": "验证码错误或已过期"
                    }
                }
            ],
            "edges": [
                {"edge_id": "e1", "source_node_id": "trigger_1", "target_node_id": "validate_1"},
                {"edge_id": "e2", "source_node_id": "validate_1", "target_node_id": "condition_verification"},
                {"edge_id": "e3", "source_node_id": "condition_verification", "target_node_id": "generate_code", "source_handle": "true", "label": "是"},
                {"edge_id": "e4", "source_node_id": "condition_verification", "target_node_id": "create_user", "source_handle": "false", "label": "否"},
                {"edge_id": "e5", "source_node_id": "generate_code", "target_node_id": "send_verification"},
                {"edge_id": "e6", "source_node_id": "send_verification", "target_node_id": "wait_verify"},
                {"edge_id": "e7", "source_node_id": "wait_verify", "target_node_id": "verify_code"},
                {"edge_id": "e8", "source_node_id": "verify_code", "target_node_id": "create_user", "source_handle": "valid", "label": "通过"},
                {"edge_id": "e9", "source_node_id": "verify_code", "target_node_id": "end_failed", "source_handle": "invalid", "label": "失败"},
                {"edge_id": "e10", "source_node_id": "create_user", "target_node_id": "condition_welcome"},
                {"edge_id": "e11", "source_node_id": "condition_welcome", "target_node_id": "send_welcome", "source_handle": "true", "label": "是"},
                {"edge_id": "e12", "source_node_id": "condition_welcome", "target_node_id": "condition_notify_admin", "source_handle": "false", "label": "否"},
                {"edge_id": "e13", "source_node_id": "send_welcome", "target_node_id": "condition_notify_admin"},
                {"edge_id": "e14", "source_node_id": "condition_notify_admin", "target_node_id": "notify_admin", "source_handle": "true", "label": "是"},
                {"edge_id": "e15", "source_node_id": "condition_notify_admin", "target_node_id": "end_success", "source_handle": "false", "label": "否"},
                {"edge_id": "e16", "source_node_id": "notify_admin", "target_node_id": "end_success"}
            ],
            "config_schema": {
                "type": "object",
                "properties": {
                    "require_verification": {
                        "type": "boolean",
                        "title": "需要邮箱验证",
                        "description": "注册时是否需要验证邮箱",
                        "default": True
                    },
                    "require_invite_code": {
                        "type": "boolean",
                        "title": "需要邀请码",
                        "description": "注册时是否需要邀请码",
                        "default": True
                    },
                    "send_welcome_email": {
                        "type": "boolean",
                        "title": "发送欢迎邮件",
                        "description": "注册成功后是否发送欢迎邮件",
                        "default": True
                    },
                    "notify_admin": {
                        "type": "boolean",
                        "title": "通知管理员",
                        "description": "新用户注册时是否通知管理员",
                        "default": False
                    },
                    "verification_code_expire_minutes": {
                        "type": "integer",
                        "title": "验证码有效期(分钟)",
                        "default": 15,
                        "minimum": 1,
                        "maximum": 60
                    },
                    "verification_code_length": {
                        "type": "integer",
                        "title": "验证码长度",
                        "default": 6,
                        "minimum": 4,
                        "maximum": 8
                    },
                    "password_min_length": {
                        "type": "integer",
                        "title": "密码最小长度",
                        "default": 8,
                        "minimum": 6,
                        "maximum": 32
                    }
                }
            },
            "default_config": {
                "require_verification": True,
                "require_invite_code": True,
                "send_welcome_email": True,
                "notify_admin": False,
                "verification_code_expire_minutes": 15,
                "verification_code_length": 6,
                "password_min_length": 8
            }
        },
        {
            "code": "password_reset",
            "name": "密码重置流程",
            "name_en": "Password Reset",
            "description": "处理用户密码重置的完整流程",
            "category": "auth",
            "trigger_event": "password.forgot",
            "nodes": [
                {
                    "node_id": "trigger_1",
                    "node_type": "trigger",
                    "node_subtype": "trigger_form_submit",
                    "name": "请求重置密码",
                    "position_x": 250,
                    "position_y": 50,
                    "is_system": True
                },
                {
                    "node_id": "check_user",
                    "node_type": "logic",
                    "node_subtype": "logic_condition",
                    "name": "用户是否存在",
                    "position_x": 250,
                    "position_y": 150
                },
                {
                    "node_id": "generate_code",
                    "node_type": "data",
                    "node_subtype": "data_generate_code",
                    "name": "生成重置验证码",
                    "position_x": 100,
                    "position_y": 250
                },
                {
                    "node_id": "send_reset",
                    "node_type": "action",
                    "node_subtype": "action_send_template",
                    "name": "发送重置邮件",
                    "position_x": 100,
                    "position_y": 350,
                    "config": {
                        "template_code": "verification_code_reset_password",
                        "to_type": "form_field",
                        "to_field": "email"
                    }
                },
                {
                    "node_id": "wait_verify",
                    "node_type": "logic",
                    "node_subtype": "logic_wait",
                    "name": "等待用户验证",
                    "position_x": 100,
                    "position_y": 450
                },
                {
                    "node_id": "verify_code",
                    "node_type": "data",
                    "node_subtype": "data_verify_code",
                    "name": "校验验证码",
                    "position_x": 100,
                    "position_y": 550
                },
                {
                    "node_id": "update_password",
                    "node_type": "data",
                    "node_subtype": "data_update_user",
                    "name": "更新密码",
                    "position_x": 100,
                    "position_y": 650,
                    "is_system": True
                },
                {
                    "node_id": "send_confirmation",
                    "node_type": "action",
                    "node_subtype": "action_send_template",
                    "name": "发送确认邮件",
                    "position_x": 100,
                    "position_y": 750,
                    "config": {
                        "template_code": "password_changed",
                        "to_type": "trigger_user"
                    }
                },
                {
                    "node_id": "end_success",
                    "node_type": "end",
                    "node_subtype": "end_success",
                    "name": "重置成功",
                    "position_x": 100,
                    "position_y": 850
                },
                {
                    "node_id": "end_not_found",
                    "node_type": "end",
                    "node_subtype": "end_success",
                    "name": "处理完成(安全)",
                    "position_x": 400,
                    "position_y": 250,
                    "config": {
                        "message": "如果该邮箱已注册，您将收到重置邮件"
                    }
                },
                {
                    "node_id": "end_failed",
                    "node_type": "end",
                    "node_subtype": "end_failure",
                    "name": "验证失败",
                    "position_x": 300,
                    "position_y": 650
                }
            ],
            "edges": [
                {"edge_id": "e1", "source_node_id": "trigger_1", "target_node_id": "check_user"},
                {"edge_id": "e2", "source_node_id": "check_user", "target_node_id": "generate_code", "source_handle": "true"},
                {"edge_id": "e3", "source_node_id": "check_user", "target_node_id": "end_not_found", "source_handle": "false"},
                {"edge_id": "e4", "source_node_id": "generate_code", "target_node_id": "send_reset"},
                {"edge_id": "e5", "source_node_id": "send_reset", "target_node_id": "wait_verify"},
                {"edge_id": "e6", "source_node_id": "wait_verify", "target_node_id": "verify_code"},
                {"edge_id": "e7", "source_node_id": "verify_code", "target_node_id": "update_password", "source_handle": "valid"},
                {"edge_id": "e8", "source_node_id": "verify_code", "target_node_id": "end_failed", "source_handle": "invalid"},
                {"edge_id": "e9", "source_node_id": "update_password", "target_node_id": "send_confirmation"},
                {"edge_id": "e10", "source_node_id": "send_confirmation", "target_node_id": "end_success"}
            ],
            "config_schema": {
                "type": "object",
                "properties": {
                    "reset_method": {
                        "type": "string",
                        "title": "重置方式",
                        "enum": ["code", "link"],
                        "enumNames": ["验证码", "链接"],
                        "default": "code"
                    },
                    "code_expire_minutes": {
                        "type": "integer",
                        "title": "验证码有效期(分钟)",
                        "default": 15
                    },
                    "send_confirmation": {
                        "type": "boolean",
                        "title": "发送确认邮件",
                        "default": True
                    },
                    "hide_user_not_found": {
                        "type": "boolean",
                        "title": "隐藏用户不存在错误",
                        "description": "为安全起见，不显示邮箱是否已注册",
                        "default": True
                    }
                }
            },
            "default_config": {
                "reset_method": "code",
                "code_expire_minutes": 15,
                "send_confirmation": True,
                "hide_user_not_found": True
            }
        },
        {
            "code": "user_login",
            "name": "用户登录流程",
            "name_en": "User Login",
            "description": "处理用户登录的安全流程",
            "category": "auth",
            "nodes": [
                {
                    "node_id": "trigger_1",
                    "node_type": "trigger",
                    "node_subtype": "trigger_form_submit",
                    "name": "提交登录表单",
                    "position_x": 250,
                    "position_y": 50
                },
                {
                    "node_id": "verify_password",
                    "node_type": "data",
                    "node_subtype": "data_verify_password",
                    "name": "验证密码",
                    "position_x": 250,
                    "position_y": 150
                },
                {
                    "node_id": "check_new_device",
                    "node_type": "logic",
                    "node_subtype": "logic_condition",
                    "name": "是否新设备",
                    "position_x": 100,
                    "position_y": 250
                },
                {
                    "node_id": "send_alert",
                    "node_type": "action",
                    "node_subtype": "action_send_template",
                    "name": "发送安全提醒",
                    "position_x": 50,
                    "position_y": 350,
                    "config": {
                        "template_code": "login_alert",
                        "to_type": "trigger_user"
                    }
                },
                {
                    "node_id": "check_2fa",
                    "node_type": "logic",
                    "node_subtype": "logic_condition",
                    "name": "需要2FA",
                    "position_x": 250,
                    "position_y": 450
                },
                {
                    "node_id": "verify_2fa",
                    "node_type": "logic",
                    "node_subtype": "logic_wait",
                    "name": "验证2FA",
                    "position_x": 100,
                    "position_y": 550
                },
                {
                    "node_id": "end_success",
                    "node_type": "end",
                    "node_subtype": "end_success",
                    "name": "登录成功",
                    "position_x": 250,
                    "position_y": 650
                },
                {
                    "node_id": "record_failed",
                    "node_type": "data",
                    "node_subtype": "data_update_user",
                    "name": "记录失败次数",
                    "position_x": 400,
                    "position_y": 250
                },
                {
                    "node_id": "check_lockout",
                    "node_type": "logic",
                    "node_subtype": "logic_condition",
                    "name": "是否锁定",
                    "position_x": 400,
                    "position_y": 350
                },
                {
                    "node_id": "send_lockout",
                    "node_type": "action",
                    "node_subtype": "action_send_template",
                    "name": "发送锁定通知",
                    "position_x": 500,
                    "position_y": 450
                },
                {
                    "node_id": "end_failed",
                    "node_type": "end",
                    "node_subtype": "end_failure",
                    "name": "登录失败",
                    "position_x": 400,
                    "position_y": 550
                }
            ],
            "edges": [
                {"edge_id": "e1", "source_node_id": "trigger_1", "target_node_id": "verify_password"},
                {"edge_id": "e2", "source_node_id": "verify_password", "target_node_id": "check_new_device", "source_handle": "valid"},
                {"edge_id": "e3", "source_node_id": "verify_password", "target_node_id": "record_failed", "source_handle": "invalid"},
                {"edge_id": "e4", "source_node_id": "check_new_device", "target_node_id": "send_alert", "source_handle": "true"},
                {"edge_id": "e5", "source_node_id": "check_new_device", "target_node_id": "check_2fa", "source_handle": "false"},
                {"edge_id": "e6", "source_node_id": "send_alert", "target_node_id": "check_2fa"},
                {"edge_id": "e7", "source_node_id": "check_2fa", "target_node_id": "verify_2fa", "source_handle": "true"},
                {"edge_id": "e8", "source_node_id": "check_2fa", "target_node_id": "end_success", "source_handle": "false"},
                {"edge_id": "e9", "source_node_id": "verify_2fa", "target_node_id": "end_success"},
                {"edge_id": "e10", "source_node_id": "record_failed", "target_node_id": "check_lockout"},
                {"edge_id": "e11", "source_node_id": "check_lockout", "target_node_id": "send_lockout", "source_handle": "true"},
                {"edge_id": "e12", "source_node_id": "check_lockout", "target_node_id": "end_failed", "source_handle": "false"},
                {"edge_id": "e13", "source_node_id": "send_lockout", "target_node_id": "end_failed"}
            ],
            "config_schema": {
                "type": "object",
                "properties": {
                    "max_failed_attempts": {
                        "type": "integer",
                        "title": "最大失败次数",
                        "default": 5
                    },
                    "lockout_duration_minutes": {
                        "type": "integer",
                        "title": "锁定时长(分钟)",
                        "default": 30
                    },
                    "notify_new_device": {
                        "type": "boolean",
                        "title": "新设备登录通知",
                        "default": True
                    },
                    "require_2fa": {
                        "type": "boolean",
                        "title": "强制2FA",
                        "default": False
                    }
                }
            },
            "default_config": {
                "max_failed_attempts": 5,
                "lockout_duration_minutes": 30,
                "notify_new_device": True,
                "require_2fa": False
            }
        }
    ]
    
    for data in system_workflows:
        # Check if exists by code
        existing_wf = db.query(SystemWorkflow).filter(SystemWorkflow.code == data["code"]).first()
        if existing_wf:
            # Update fields if needed (especially trigger_event)
            existing_wf.trigger_event = data.get("trigger_event")
            # You might want to update nodes/edges too, but be careful not to overwrite user customizations
            # For now, we only patch the critical trigger_event
            print(f"更新现有工作流 {data['code']} 的 trigger_event")
        else:
            workflow = SystemWorkflow(
                code=data["code"],
                name=data["name"],
                name_en=data.get("name_en"),
                description=data.get("description"),
                category=data["category"],
                trigger_event=data.get("trigger_event"),
                nodes=data["nodes"],
                edges=data["edges"],
                config_schema=data.get("config_schema"),
                default_config=data.get("default_config", {}),
                is_active=True
            )
            db.add(workflow)
    
    db.commit()
    print(f"成功初始化/更新 {len(system_workflows)} 个系统工作流")


def init_all_workflow_data(db: Session):
    """初始化所有工作流数据"""
    print("开始初始化工作流数据...")
    init_node_types(db)
    init_system_workflows(db)
    print("工作流数据初始化完成！")


if __name__ == "__main__":
    from db.database import SessionLocal
    db = SessionLocal()
    try:
        init_all_workflow_data(db)
    finally:
        db.close()