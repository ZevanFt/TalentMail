"""
初始化工作流模板数据
创建常用的、有实用价值的工作流模板
"""
import logging
from sqlalchemy.orm import Session
from db.models.workflow import WorkflowTemplate, WorkflowTemplateTag
from db.database import SessionLocal

logger = logging.getLogger(__name__)


# 模板数据定义
WORKFLOW_TEMPLATES = [
    # ========== 邮件处理类 ==========
    {
        "name": "重要邮件自动标星",
        "name_en": "Auto Star Important Emails",
        "description": "当收到来自通讯录中联系人或主题包含「紧急」「重要」的邮件时，自动标记为星标，确保不会错过重要信息。",
        "description_en": "Automatically star emails from contacts or with urgent keywords in subject.",
        "category": "email",
        "is_featured": True,
        "tags": ["邮件处理", "自动标记", "效率提升"],
        "nodes": [
            {
                "node_id": "trigger_1",
                "node_type": "trigger",
                "node_subtype": "trigger_email_received",
                "name": "收到邮件",
                "position_x": 250,
                "position_y": 50,
                "config": {}
            },
            {
                "node_id": "condition_1",
                "node_type": "logic",
                "node_subtype": "logic_condition",
                "name": "是重要邮件？",
                "position_x": 250,
                "position_y": 170,
                "config": {
                    "logic": "or",
                    "conditions": [
                        {"field": "from_contact", "operator": "equals", "value": True},
                        {"field": "subject", "operator": "contains", "value": "紧急"},
                        {"field": "subject", "operator": "contains", "value": "重要"},
                        {"field": "subject", "operator": "contains", "value": "urgent"}
                    ]
                }
            },
            {
                "node_id": "action_star",
                "node_type": "email_operation",
                "node_subtype": "operation_mark_starred",
                "name": "标记星标",
                "position_x": 100,
                "position_y": 320,
                "config": {}
            },
            {
                "node_id": "end_done",
                "node_type": "end",
                "node_subtype": "end_success",
                "name": "完成",
                "position_x": 100,
                "position_y": 440,
                "config": {"message": "已标记为星标"}
            },
            {
                "node_id": "end_skip",
                "node_type": "end",
                "node_subtype": "end_success",
                "name": "跳过",
                "position_x": 400,
                "position_y": 320,
                "config": {"message": "非重要邮件，跳过"}
            }
        ],
        "edges": [
            {"edge_id": "e1", "source_node_id": "trigger_1", "target_node_id": "condition_1"},
            {"edge_id": "e2", "source_node_id": "condition_1", "target_node_id": "action_star", "source_handle": "true", "label": "是"},
            {"edge_id": "e3", "source_node_id": "condition_1", "target_node_id": "end_skip", "source_handle": "false", "label": "否"},
            {"edge_id": "e4", "source_node_id": "action_star", "target_node_id": "end_done"}
        ]
    },
    {
        "name": "VIP客户邮件提醒",
        "name_en": "VIP Customer Email Alert",
        "description": "当收到来自 VIP 客户的邮件时，自动标记星标并添加「VIP」标签，确保及时响应重要客户。",
        "description_en": "Auto star and tag emails from VIP customers for priority handling.",
        "category": "email",
        "is_featured": True,
        "tags": ["客户管理", "VIP", "邮件处理"],
        "nodes": [
            {
                "node_id": "trigger_1",
                "node_type": "trigger",
                "node_subtype": "trigger_email_received",
                "name": "收到邮件",
                "position_x": 250,
                "position_y": 50,
                "config": {}
            },
            {
                "node_id": "condition_vip",
                "node_type": "logic",
                "node_subtype": "logic_condition",
                "name": "是VIP客户？",
                "position_x": 250,
                "position_y": 170,
                "config": {
                    "logic": "or",
                    "conditions": [
                        {"field": "sender_domain", "operator": "equals", "value": "vip-client.com"},
                        {"field": "sender_email", "operator": "in_list", "value": "vip_customers"}
                    ]
                }
            },
            {
                "node_id": "action_star",
                "node_type": "email_operation",
                "node_subtype": "operation_mark_starred",
                "name": "标记星标",
                "position_x": 100,
                "position_y": 320,
                "config": {}
            },
            {
                "node_id": "action_tag",
                "node_type": "email_operation",
                "node_subtype": "operation_add_tag",
                "name": "添加VIP标签",
                "position_x": 100,
                "position_y": 440,
                "config": {"tag_name": "VIP"}
            },
            {
                "node_id": "end_done",
                "node_type": "end",
                "node_subtype": "end_success",
                "name": "完成",
                "position_x": 100,
                "position_y": 560,
                "config": {"message": "VIP邮件已标记"}
            },
            {
                "node_id": "end_skip",
                "node_type": "end",
                "node_subtype": "end_success",
                "name": "跳过",
                "position_x": 400,
                "position_y": 320,
                "config": {}
            }
        ],
        "edges": [
            {"edge_id": "e1", "source_node_id": "trigger_1", "target_node_id": "condition_vip"},
            {"edge_id": "e2", "source_node_id": "condition_vip", "target_node_id": "action_star", "source_handle": "true", "label": "是"},
            {"edge_id": "e3", "source_node_id": "condition_vip", "target_node_id": "end_skip", "source_handle": "false", "label": "否"},
            {"edge_id": "e4", "source_node_id": "action_star", "target_node_id": "action_tag"},
            {"edge_id": "e5", "source_node_id": "action_tag", "target_node_id": "end_done"}
        ]
    },
    {
        "name": "垃圾邮件自动归档",
        "name_en": "Auto Archive Spam",
        "description": "自动识别垃圾邮件（包含广告关键词或发件人在黑名单中），并移动到垃圾箱，保持收件箱整洁。",
        "description_en": "Automatically detect and move spam emails to trash folder.",
        "category": "email",
        "is_featured": True,
        "tags": ["垃圾邮件", "自动清理", "邮件处理"],
        "nodes": [
            {
                "node_id": "trigger_1",
                "node_type": "trigger",
                "node_subtype": "trigger_email_received",
                "name": "收到邮件",
                "position_x": 250,
                "position_y": 50,
                "config": {}
            },
            {
                "node_id": "condition_spam",
                "node_type": "logic",
                "node_subtype": "logic_condition",
                "name": "是垃圾邮件？",
                "position_x": 250,
                "position_y": 170,
                "config": {
                    "logic": "or",
                    "conditions": [
                        {"field": "sender_blocked", "operator": "equals", "value": True},
                        {"field": "subject", "operator": "contains", "value": "免费"},
                        {"field": "subject", "operator": "contains", "value": "中奖"},
                        {"field": "subject", "operator": "contains", "value": "优惠"},
                        {"field": "subject", "operator": "matches_regex", "value": "\\d+%\\s*off"}
                    ]
                }
            },
            {
                "node_id": "action_trash",
                "node_type": "email_operation",
                "node_subtype": "operation_move_to_folder",
                "name": "移到垃圾箱",
                "position_x": 100,
                "position_y": 320,
                "config": {"folder": "trash"}
            },
            {
                "node_id": "end_done",
                "node_type": "end",
                "node_subtype": "end_success",
                "name": "已归档",
                "position_x": 100,
                "position_y": 440,
                "config": {"message": "垃圾邮件已移到垃圾箱"}
            },
            {
                "node_id": "end_skip",
                "node_type": "end",
                "node_subtype": "end_success",
                "name": "正常邮件",
                "position_x": 400,
                "position_y": 320,
                "config": {}
            }
        ],
        "edges": [
            {"edge_id": "e1", "source_node_id": "trigger_1", "target_node_id": "condition_spam"},
            {"edge_id": "e2", "source_node_id": "condition_spam", "target_node_id": "action_trash", "source_handle": "true", "label": "是"},
            {"edge_id": "e3", "source_node_id": "condition_spam", "target_node_id": "end_skip", "source_handle": "false", "label": "否"},
            {"edge_id": "e4", "source_node_id": "action_trash", "target_node_id": "end_done"}
        ]
    },
    {
        "name": "自动整理订阅邮件",
        "name_en": "Auto Organize Newsletters",
        "description": "自动识别订阅邮件和通知邮件，添加「订阅」标签并移动到指定文件夹，保持收件箱专注于重要邮件。",
        "description_en": "Auto categorize newsletters and notifications into dedicated folder.",
        "category": "email",
        "is_featured": False,
        "tags": ["订阅管理", "邮件整理", "效率提升"],
        "nodes": [
            {
                "node_id": "trigger_1",
                "node_type": "trigger",
                "node_subtype": "trigger_email_received",
                "name": "收到邮件",
                "position_x": 250,
                "position_y": 50,
                "config": {}
            },
            {
                "node_id": "condition_newsletter",
                "node_type": "logic",
                "node_subtype": "logic_condition",
                "name": "是订阅邮件？",
                "position_x": 250,
                "position_y": 170,
                "config": {
                    "logic": "or",
                    "conditions": [
                        {"field": "sender_email", "operator": "contains", "value": "newsletter"},
                        {"field": "sender_email", "operator": "contains", "value": "noreply"},
                        {"field": "sender_email", "operator": "contains", "value": "notification"},
                        {"field": "headers.List-Unsubscribe", "operator": "is_not_empty", "value": ""}
                    ]
                }
            },
            {
                "node_id": "action_tag",
                "node_type": "email_operation",
                "node_subtype": "operation_add_tag",
                "name": "添加订阅标签",
                "position_x": 100,
                "position_y": 320,
                "config": {"tag_name": "订阅"}
            },
            {
                "node_id": "action_move",
                "node_type": "email_operation",
                "node_subtype": "operation_move_to_folder",
                "name": "移到订阅文件夹",
                "position_x": 100,
                "position_y": 440,
                "config": {"folder": "newsletters"}
            },
            {
                "node_id": "end_done",
                "node_type": "end",
                "node_subtype": "end_success",
                "name": "已整理",
                "position_x": 100,
                "position_y": 560,
                "config": {}
            },
            {
                "node_id": "end_skip",
                "node_type": "end",
                "node_subtype": "end_success",
                "name": "跳过",
                "position_x": 400,
                "position_y": 320,
                "config": {}
            }
        ],
        "edges": [
            {"edge_id": "e1", "source_node_id": "trigger_1", "target_node_id": "condition_newsletter"},
            {"edge_id": "e2", "source_node_id": "condition_newsletter", "target_node_id": "action_tag", "source_handle": "true", "label": "是"},
            {"edge_id": "e3", "source_node_id": "condition_newsletter", "target_node_id": "end_skip", "source_handle": "false", "label": "否"},
            {"edge_id": "e4", "source_node_id": "action_tag", "target_node_id": "action_move"},
            {"edge_id": "e5", "source_node_id": "action_move", "target_node_id": "end_done"}
        ]
    },
    
    # ========== 自动回复类 ==========
    {
        "name": "收到询盘自动回复",
        "name_en": "Auto Reply to Inquiries",
        "description": "当收到包含「询价」「报价」等关键词的邮件时，自动发送确认邮件，让客户知道您已收到并会尽快处理。",
        "description_en": "Automatically send confirmation email when receiving inquiries.",
        "category": "notification",
        "is_featured": True,
        "tags": ["自动回复", "客户服务", "询盘处理"],
        "nodes": [
            {
                "node_id": "trigger_1",
                "node_type": "trigger",
                "node_subtype": "trigger_email_received",
                "name": "收到邮件",
                "position_x": 250,
                "position_y": 50,
                "config": {}
            },
            {
                "node_id": "condition_inquiry",
                "node_type": "logic",
                "node_subtype": "logic_condition",
                "name": "是询盘邮件？",
                "position_x": 250,
                "position_y": 170,
                "config": {
                    "logic": "or",
                    "conditions": [
                        {"field": "subject", "operator": "contains", "value": "询价"},
                        {"field": "subject", "operator": "contains", "value": "报价"},
                        {"field": "subject", "operator": "contains", "value": "询盘"},
                        {"field": "subject", "operator": "contains", "value": "quote"},
                        {"field": "subject", "operator": "contains", "value": "inquiry"}
                    ]
                }
            },
            {
                "node_id": "action_reply",
                "node_type": "email_action",
                "node_subtype": "action_auto_reply",
                "name": "自动回复",
                "position_x": 100,
                "position_y": 320,
                "config": {
                    "template_code": "inquiry_auto_reply",
                    "subject": "Re: 感谢您的询价 - 我们已收到",
                    "body": "您好，\n\n感谢您的询价邮件，我们已收到您的需求。\n\n我们的销售团队会在1-2个工作日内与您联系，提供详细报价。\n\n如有紧急需求，请直接回复此邮件或拨打我们的服务热线。\n\n祝好！"
                }
            },
            {
                "node_id": "action_tag",
                "node_type": "email_operation",
                "node_subtype": "operation_add_tag",
                "name": "添加询盘标签",
                "position_x": 100,
                "position_y": 440,
                "config": {"tag_name": "询盘"}
            },
            {
                "node_id": "end_done",
                "node_type": "end",
                "node_subtype": "end_success",
                "name": "已回复",
                "position_x": 100,
                "position_y": 560,
                "config": {"message": "询盘已自动回复"}
            },
            {
                "node_id": "end_skip",
                "node_type": "end",
                "node_subtype": "end_success",
                "name": "跳过",
                "position_x": 400,
                "position_y": 320,
                "config": {}
            }
        ],
        "edges": [
            {"edge_id": "e1", "source_node_id": "trigger_1", "target_node_id": "condition_inquiry"},
            {"edge_id": "e2", "source_node_id": "condition_inquiry", "target_node_id": "action_reply", "source_handle": "true", "label": "是"},
            {"edge_id": "e3", "source_node_id": "condition_inquiry", "target_node_id": "end_skip", "source_handle": "false", "label": "否"},
            {"edge_id": "e4", "source_node_id": "action_reply", "target_node_id": "action_tag"},
            {"edge_id": "e5", "source_node_id": "action_tag", "target_node_id": "end_done"}
        ]
    },
    {
        "name": "休假自动回复",
        "name_en": "Vacation Auto Reply",
        "description": "设置休假期间的自动回复，让发件人知道您目前不在办公室，并提供紧急联系方式。",
        "description_en": "Automatically reply to all emails during vacation with out-of-office message.",
        "category": "notification",
        "is_featured": True,
        "tags": ["自动回复", "休假", "办公效率"],
        "nodes": [
            {
                "node_id": "trigger_1",
                "node_type": "trigger",
                "node_subtype": "trigger_email_received",
                "name": "收到邮件",
                "position_x": 250,
                "position_y": 50,
                "config": {}
            },
            {
                "node_id": "condition_not_auto",
                "node_type": "logic",
                "node_subtype": "logic_condition",
                "name": "非自动邮件？",
                "position_x": 250,
                "position_y": 170,
                "config": {
                    "logic": "and",
                    "conditions": [
                        {"field": "sender_email", "operator": "not_contains", "value": "noreply"},
                        {"field": "sender_email", "operator": "not_contains", "value": "mailer-daemon"},
                        {"field": "headers.Auto-Submitted", "operator": "is_empty", "value": ""}
                    ]
                }
            },
            {
                "node_id": "action_reply",
                "node_type": "email_action",
                "node_subtype": "action_auto_reply",
                "name": "发送休假回复",
                "position_x": 100,
                "position_y": 320,
                "config": {
                    "template_code": "vacation_reply",
                    "subject": "Re: 自动回复 - 我正在休假中",
                    "body": "您好，\n\n感谢您的来信。我目前正在休假中，将于 [返回日期] 回到工作岗位。\n\n休假期间我可能无法及时回复邮件。如有紧急事务，请联系 [紧急联系人] 或拨打 [紧急电话]。\n\n感谢您的理解！\n\n祝好"
                }
            },
            {
                "node_id": "end_done",
                "node_type": "end",
                "node_subtype": "end_success",
                "name": "已回复",
                "position_x": 100,
                "position_y": 440,
                "config": {}
            },
            {
                "node_id": "end_skip",
                "node_type": "end",
                "node_subtype": "end_success",
                "name": "跳过自动邮件",
                "position_x": 400,
                "position_y": 320,
                "config": {}
            }
        ],
        "edges": [
            {"edge_id": "e1", "source_node_id": "trigger_1", "target_node_id": "condition_not_auto"},
            {"edge_id": "e2", "source_node_id": "condition_not_auto", "target_node_id": "action_reply", "source_handle": "true", "label": "是"},
            {"edge_id": "e3", "source_node_id": "condition_not_auto", "target_node_id": "end_skip", "source_handle": "false", "label": "否"},
            {"edge_id": "e4", "source_node_id": "action_reply", "target_node_id": "end_done"}
        ]
    },
    
    # ========== 转发类 ==========
    {
        "name": "重要邮件转发给团队",
        "name_en": "Forward Important Emails to Team",
        "description": "当收到包含「合同」「付款」等关键词的邮件时，自动转发给指定的团队成员，确保团队及时知晓重要信息。",
        "description_en": "Auto forward emails with important keywords to team members.",
        "category": "automation",
        "is_featured": False,
        "tags": ["邮件转发", "团队协作", "自动化"],
        "nodes": [
            {
                "node_id": "trigger_1",
                "node_type": "trigger",
                "node_subtype": "trigger_email_received",
                "name": "收到邮件",
                "position_x": 250,
                "position_y": 50,
                "config": {}
            },
            {
                "node_id": "condition_important",
                "node_type": "logic",
                "node_subtype": "logic_condition",
                "name": "包含重要关键词？",
                "position_x": 250,
                "position_y": 170,
                "config": {
                    "logic": "or",
                    "conditions": [
                        {"field": "subject", "operator": "contains", "value": "合同"},
                        {"field": "subject", "operator": "contains", "value": "付款"},
                        {"field": "subject", "operator": "contains", "value": "签约"},
                        {"field": "subject", "operator": "contains", "value": "contract"},
                        {"field": "subject", "operator": "contains", "value": "payment"}
                    ]
                }
            },
            {
                "node_id": "action_forward",
                "node_type": "email_action",
                "node_subtype": "action_forward",
                "name": "转发给团队",
                "position_x": 100,
                "position_y": 320,
                "config": {
                    "to": "team@example.com",
                    "add_note": "【自动转发】此邮件包含重要业务关键词，请及时处理。"
                }
            },
            {
                "node_id": "action_tag",
                "node_type": "email_operation",
                "node_subtype": "operation_add_tag",
                "name": "添加已转发标签",
                "position_x": 100,
                "position_y": 440,
                "config": {"tag_name": "已转发"}
            },
            {
                "node_id": "end_done",
                "node_type": "end",
                "node_subtype": "end_success",
                "name": "已转发",
                "position_x": 100,
                "position_y": 560,
                "config": {}
            },
            {
                "node_id": "end_skip",
                "node_type": "end",
                "node_subtype": "end_success",
                "name": "跳过",
                "position_x": 400,
                "position_y": 320,
                "config": {}
            }
        ],
        "edges": [
            {"edge_id": "e1", "source_node_id": "trigger_1", "target_node_id": "condition_important"},
            {"edge_id": "e2", "source_node_id": "condition_important", "target_node_id": "action_forward", "source_handle": "true", "label": "是"},
            {"edge_id": "e3", "source_node_id": "condition_important", "target_node_id": "end_skip", "source_handle": "false", "label": "否"},
            {"edge_id": "e4", "source_node_id": "action_forward", "target_node_id": "action_tag"},
            {"edge_id": "e5", "source_node_id": "action_tag", "target_node_id": "end_done"}
        ]
    },
    {
        "name": "客户投诉转发给负责人",
        "name_en": "Forward Complaints to Manager",
        "description": "当收到包含「投诉」「问题」「不满」等关键词的邮件时，自动转发给客服主管并标记为待处理，确保投诉及时得到重视。",
        "description_en": "Auto forward complaint emails to customer service manager.",
        "category": "automation",
        "is_featured": False,
        "tags": ["客户服务", "投诉处理", "邮件转发"],
        "nodes": [
            {
                "node_id": "trigger_1",
                "node_type": "trigger",
                "node_subtype": "trigger_email_received",
                "name": "收到邮件",
                "position_x": 250,
                "position_y": 50,
                "config": {}
            },
            {
                "node_id": "condition_complaint",
                "node_type": "logic",
                "node_subtype": "logic_condition",
                "name": "是投诉邮件？",
                "position_x": 250,
                "position_y": 170,
                "config": {
                    "logic": "or",
                    "conditions": [
                        {"field": "subject", "operator": "contains", "value": "投诉"},
                        {"field": "subject", "operator": "contains", "value": "问题"},
                        {"field": "subject", "operator": "contains", "value": "不满"},
                        {"field": "subject", "operator": "contains", "value": "complaint"},
                        {"field": "body", "operator": "contains", "value": "差评"}
                    ]
                }
            },
            {
                "node_id": "action_forward",
                "node_type": "email_action",
                "node_subtype": "action_forward",
                "name": "转发给主管",
                "position_x": 100,
                "position_y": 320,
                "config": {
                    "to": "manager@example.com",
                    "add_note": "【客户投诉】此邮件包含投诉相关内容，请优先处理。"
                }
            },
            {
                "node_id": "action_tag",
                "node_type": "email_operation",
                "node_subtype": "operation_add_tag",
                "name": "添加待处理标签",
                "position_x": 100,
                "position_y": 440,
                "config": {"tag_name": "待处理"}
            },
            {
                "node_id": "action_star",
                "node_type": "email_operation",
                "node_subtype": "operation_mark_starred",
                "name": "标记星标",
                "position_x": 100,
                "position_y": 560,
                "config": {}
            },
            {
                "node_id": "end_done",
                "node_type": "end",
                "node_subtype": "end_success",
                "name": "已处理",
                "position_x": 100,
                "position_y": 680,
                "config": {}
            },
            {
                "node_id": "end_skip",
                "node_type": "end",
                "node_subtype": "end_success",
                "name": "跳过",
                "position_x": 400,
                "position_y": 320,
                "config": {}
            }
        ],
        "edges": [
            {"edge_id": "e1", "source_node_id": "trigger_1", "target_node_id": "condition_complaint"},
            {"edge_id": "e2", "source_node_id": "condition_complaint", "target_node_id": "action_forward", "source_handle": "true", "label": "是"},
            {"edge_id": "e3", "source_node_id": "condition_complaint", "target_node_id": "end_skip", "source_handle": "false", "label": "否"},
            {"edge_id": "e4", "source_node_id": "action_forward", "target_node_id": "action_tag"},
            {"edge_id": "e5", "source_node_id": "action_tag", "target_node_id": "action_star"},
            {"edge_id": "e6", "source_node_id": "action_star", "target_node_id": "end_done"}
        ]
    },
    
    # ========== 智能分类 ==========
    {
        "name": "项目邮件自动归类",
        "name_en": "Auto Categorize Project Emails",
        "description": "根据邮件主题中的项目名称，自动添加对应的项目标签并移动到项目文件夹，方便按项目管理邮件。",
        "description_en": "Auto tag and organize emails based on project name in subject.",
        "category": "email",
        "is_featured": False,
        "tags": ["项目管理", "邮件分类", "效率提升"],
        "nodes": [
            {
                "node_id": "trigger_1",
                "node_type": "trigger",
                "node_subtype": "trigger_email_received",
                "name": "收到邮件",
                "position_x": 250,
                "position_y": 50,
                "config": {}
            },
            {
                "node_id": "condition_project",
                "node_type": "logic",
                "node_subtype": "logic_condition",
                "name": "包含项目名？",
                "position_x": 250,
                "position_y": 170,
                "config": {
                    "logic": "or",
                    "conditions": [
                        {"field": "subject", "operator": "matches_regex", "value": "\\[项目.+\\]"},
                        {"field": "subject", "operator": "matches_regex", "value": "\\[Project.+\\]"},
                        {"field": "subject", "operator": "contains", "value": "【项目"}
                    ]
                }
            },
            {
                "node_id": "action_tag",
                "node_type": "email_operation",
                "node_subtype": "operation_add_tag",
                "name": "添加项目标签",
                "position_x": 100,
                "position_y": 320,
                "config": {"tag_name": "项目邮件"}
            },
            {
                "node_id": "action_move",
                "node_type": "email_operation",
                "node_subtype": "operation_move_to_folder",
                "name": "移到项目文件夹",
                "position_x": 100,
                "position_y": 440,
                "config": {"folder": "projects"}
            },
            {
                "node_id": "end_done",
                "node_type": "end",
                "node_subtype": "end_success",
                "name": "已归类",
                "position_x": 100,
                "position_y": 560,
                "config": {}
            },
            {
                "node_id": "end_skip",
                "node_type": "end",
                "node_subtype": "end_success",
                "name": "跳过",
                "position_x": 400,
                "position_y": 320,
                "config": {}
            }
        ],
        "edges": [
            {"edge_id": "e1", "source_node_id": "trigger_1", "target_node_id": "condition_project"},
            {"edge_id": "e2", "source_node_id": "condition_project", "target_node_id": "action_tag", "source_handle": "true", "label": "是"},
            {"edge_id": "e3", "source_node_id": "condition_project", "target_node_id": "end_skip", "source_handle": "false", "label": "否"},
            {"edge_id": "e4", "source_node_id": "action_tag", "target_node_id": "action_move"},
            {"edge_id": "e5", "source_node_id": "action_move", "target_node_id": "end_done"}
        ]
    },
    {
        "name": "发票邮件自动归档",
        "name_en": "Auto Archive Invoice Emails",
        "description": "自动识别发票相关邮件，添加「财务」标签并标记星标，方便财务人员统一管理和查找。",
        "description_en": "Auto detect and organize invoice emails with finance tag.",
        "category": "email",
        "is_featured": True,
        "tags": ["财务管理", "发票", "邮件归档"],
        "nodes": [
            {
                "node_id": "trigger_1",
                "node_type": "trigger",
                "node_subtype": "trigger_email_received",
                "name": "收到邮件",
                "position_x": 250,
                "position_y": 50,
                "config": {}
            },
            {
                "node_id": "condition_invoice",
                "node_type": "logic",
                "node_subtype": "logic_condition",
                "name": "是发票邮件？",
                "position_x": 250,
                "position_y": 170,
                "config": {
                    "logic": "or",
                    "conditions": [
                        {"field": "subject", "operator": "contains", "value": "发票"},
                        {"field": "subject", "operator": "contains", "value": "invoice"},
                        {"field": "subject", "operator": "contains", "value": "收据"},
                        {"field": "subject", "operator": "contains", "value": "receipt"},
                        {"field": "has_attachment", "operator": "equals", "value": True}
                    ]
                }
            },
            {
                "node_id": "action_tag",
                "node_type": "email_operation",
                "node_subtype": "operation_add_tag",
                "name": "添加财务标签",
                "position_x": 100,
                "position_y": 320,
                "config": {"tag_name": "财务"}
            },
            {
                "node_id": "action_star",
                "node_type": "email_operation",
                "node_subtype": "operation_mark_starred",
                "name": "标记星标",
                "position_x": 100,
                "position_y": 440,
                "config": {}
            },
            {
                "node_id": "end_done",
                "node_type": "end",
                "node_subtype": "end_success",
                "name": "已归档",
                "position_x": 100,
                "position_y": 560,
                "config": {"message": "发票邮件已归档"}
            },
            {
                "node_id": "end_skip",
                "node_type": "end",
                "node_subtype": "end_success",
                "name": "跳过",
                "position_x": 400,
                "position_y": 320,
                "config": {}
            }
        ],
        "edges": [
            {"edge_id": "e1", "source_node_id": "trigger_1", "target_node_id": "condition_invoice"},
            {"edge_id": "e2", "source_node_id": "condition_invoice", "target_node_id": "action_tag", "source_handle": "true", "label": "是"},
            {"edge_id": "e3", "source_node_id": "condition_invoice", "target_node_id": "end_skip", "source_handle": "false", "label": "否"},
            {"edge_id": "e4", "source_node_id": "action_tag", "target_node_id": "action_star"},
            {"edge_id": "e5", "source_node_id": "action_star", "target_node_id": "end_done"}
        ]
    }
]


def init_workflow_templates(db: Session = None, force_update: bool = False):
    """
    初始化工作流模板
    
    Args:
        db: 数据库会话，如果为 None 则创建新会话
        force_update: 是否强制更新已存在的模板
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True
    
    try:
        created_count = 0
        updated_count = 0
        
        for template_data in WORKFLOW_TEMPLATES:
            name = template_data["name"]
            tags = template_data.pop("tags", [])
            
            # 检查模板是否存在
            existing = db.query(WorkflowTemplate).filter(
                WorkflowTemplate.name == name
            ).first()
            
            if existing:
                if force_update:
                    # 更新现有模板
                    for key, value in template_data.items():
                        setattr(existing, key, value)
                    
                    # 更新标签
                    db.query(WorkflowTemplateTag).filter(
                        WorkflowTemplateTag.template_id == existing.id
                    ).delete()
                    
                    for tag_name in tags:
                        tag = WorkflowTemplateTag(
                            template_id=existing.id,
                            tag=tag_name
                        )
                        db.add(tag)
                    
                    updated_count += 1
                    logger.info(f"更新工作流模板: {name}")
                else:
                    logger.debug(f"工作流模板已存在，跳过: {name}")
            else:
                # 创建新模板
                template = WorkflowTemplate(
                    source_type="official",
                    review_status="approved",
                    **template_data
                )
                db.add(template)
                db.flush()  # 获取 ID
                
                # 添加标签
                for tag_name in tags:
                    tag = WorkflowTemplateTag(
                        template_id=template.id,
                        tag=tag_name
                    )
                    db.add(tag)
                
                created_count += 1
                logger.info(f"创建工作流模板: {name}")
        
        db.commit()
        logger.info(f"工作流模板初始化完成: 新增 {created_count} 个, 更新 {updated_count} 个")
        
        return {"created": created_count, "updated": updated_count}
        
    except Exception as e:
        db.rollback()
        logger.error(f"初始化工作流模板失败: {e}")
        raise e
    finally:
        if should_close:
            db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_workflow_templates(force_update=True)