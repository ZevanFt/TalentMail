"""
更新工作流的配置项
- 系统工作流: 添加/更新 config_schema 和 default_config
- 用户工作流: 根据节点类型自动生成配置项
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models.workflow import SystemWorkflow, Workflow, WorkflowNode, NodeType


# ==================== 系统工作流配置定义 ====================

SYSTEM_WORKFLOW_CONFIGS = {
    # 用户注册流程
    "user_registration": {
        "config_schema": {
            "type": "object",
            "properties": {
                "require_verification": {
                    "type": "boolean",
                    "title": "需要邮箱验证",
                    "description": "注册时是否需要验证邮箱地址",
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
                "verification_code_expire_minutes": {
                    "type": "integer",
                    "title": "验证码有效期(分钟)",
                    "description": "邮箱验证码的有效时长",
                    "default": 15,
                    "minimum": 1,
                    "maximum": 60
                }
            }
        },
        "default_config": {
            "require_verification": True,
            "require_invite_code": True,
            "send_welcome_email": True,
            "verification_code_expire_minutes": 15
        }
    },

    # 用户登录流程
    "user_login": {
        "config_schema": {
            "type": "object",
            "properties": {
                "max_login_attempts": {
                    "type": "integer",
                    "title": "最大登录尝试次数",
                    "description": "账户锁定前允许的最大失败登录次数",
                    "default": 5,
                    "minimum": 3,
                    "maximum": 10
                },
                "lockout_duration_minutes": {
                    "type": "integer",
                    "title": "锁定时长(分钟)",
                    "description": "账户锁定的持续时间",
                    "default": 30,
                    "minimum": 5,
                    "maximum": 1440
                },
                "notify_new_device": {
                    "type": "boolean",
                    "title": "新设备登录通知",
                    "description": "检测到新设备登录时发送邮件通知",
                    "default": True
                },
                "session_expire_hours": {
                    "type": "integer",
                    "title": "会话有效期(小时)",
                    "description": "登录会话的有效时长",
                    "default": 24,
                    "minimum": 1,
                    "maximum": 720
                }
            }
        },
        "default_config": {
            "max_login_attempts": 5,
            "lockout_duration_minutes": 30,
            "notify_new_device": True,
            "session_expire_hours": 24
        }
    },

    # 密码重置流程
    "password_reset": {
        "config_schema": {
            "type": "object",
            "properties": {
                "token_expire_minutes": {
                    "type": "integer",
                    "title": "重置链接有效期(分钟)",
                    "description": "密码重置链接的有效时长",
                    "default": 30,
                    "minimum": 5,
                    "maximum": 120
                },
                "require_old_password": {
                    "type": "boolean",
                    "title": "需要旧密码",
                    "description": "修改密码时是否需要输入旧密码",
                    "default": False
                },
                "send_confirmation": {
                    "type": "boolean",
                    "title": "发送确认邮件",
                    "description": "密码修改成功后是否发送确认邮件",
                    "default": True
                }
            }
        },
        "default_config": {
            "token_expire_minutes": 30,
            "require_old_password": False,
            "send_confirmation": True
        }
    },

    # 密码修改通知
    "password_changed_notification": {
        "config_schema": {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "title": "启用通知",
                    "description": "密码修改后是否发送通知邮件",
                    "default": True
                },
                "include_ip_address": {
                    "type": "boolean",
                    "title": "包含IP地址",
                    "description": "邮件中是否包含操作的IP地址",
                    "default": True
                },
                "include_device_info": {
                    "type": "boolean",
                    "title": "包含设备信息",
                    "description": "邮件中是否包含设备和浏览器信息",
                    "default": True
                }
            }
        },
        "default_config": {
            "enabled": True,
            "include_ip_address": True,
            "include_device_info": True
        }
    },

    # 欢迎邮件
    "welcome_email": {
        "config_schema": {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "title": "启用欢迎邮件",
                    "description": "是否在用户注册成功后发送欢迎邮件",
                    "default": True
                },
                "delay_seconds": {
                    "type": "integer",
                    "title": "延迟发送(秒)",
                    "description": "注册后延迟多少秒发送欢迎邮件",
                    "default": 0,
                    "minimum": 0,
                    "maximum": 3600
                }
            }
        },
        "default_config": {
            "enabled": True,
            "delay_seconds": 0
        }
    },

    # 邮箱验证
    "email_verification": {
        "config_schema": {
            "type": "object",
            "properties": {
                "code_length": {
                    "type": "integer",
                    "title": "验证码长度",
                    "description": "生成的验证码位数",
                    "default": 6,
                    "minimum": 4,
                    "maximum": 8
                },
                "expire_minutes": {
                    "type": "integer",
                    "title": "有效期(分钟)",
                    "description": "验证码的有效时长",
                    "default": 15,
                    "minimum": 1,
                    "maximum": 60
                },
                "max_attempts": {
                    "type": "integer",
                    "title": "最大尝试次数",
                    "description": "验证码最多可尝试验证的次数",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10
                }
            }
        },
        "default_config": {
            "code_length": 6,
            "expire_minutes": 15,
            "max_attempts": 5
        }
    },

    # 新设备登录提醒
    "new_device_alert": {
        "config_schema": {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "title": "启用新设备提醒",
                    "description": "检测到新设备登录时是否发送提醒邮件",
                    "default": True
                },
                "include_location": {
                    "type": "boolean",
                    "title": "包含位置信息",
                    "description": "邮件中是否包含登录的地理位置信息",
                    "default": True
                },
                "include_device_info": {
                    "type": "boolean",
                    "title": "包含设备信息",
                    "description": "邮件中是否包含设备和浏览器信息",
                    "default": True
                }
            }
        },
        "default_config": {
            "enabled": True,
            "include_location": True,
            "include_device_info": True
        }
    },

    # 登录通知
    "login_notification": {
        "config_schema": {
            "type": "object",
            "properties": {
                "notify_on_every_login": {
                    "type": "boolean",
                    "title": "每次登录都通知",
                    "description": "是否在每次登录时都发送通知",
                    "default": False
                },
                "notify_new_device_only": {
                    "type": "boolean",
                    "title": "仅新设备通知",
                    "description": "仅在新设备登录时发送通知",
                    "default": True
                }
            }
        },
        "default_config": {
            "notify_on_every_login": False,
            "notify_new_device_only": True
        }
    },

    # 邮件自动转发
    "email_auto_forward": {
        "config_schema": {
            "type": "object",
            "properties": {
                "keep_original": {
                    "type": "boolean",
                    "title": "保留原邮件",
                    "description": "转发后是否保留原邮件",
                    "default": True
                },
                "add_forward_prefix": {
                    "type": "boolean",
                    "title": "添加转发前缀",
                    "description": "主题是否添加 [Fwd] 前缀",
                    "default": True
                }
            }
        },
        "default_config": {
            "keep_original": True,
            "add_forward_prefix": True
        }
    },

    # 邮件自动回复
    "email_auto_reply": {
        "config_schema": {
            "type": "object",
            "properties": {
                "reply_once_per_sender": {
                    "type": "boolean",
                    "title": "每个发件人只回复一次",
                    "description": "同一发件人在一定时间内只自动回复一次",
                    "default": True
                },
                "cooldown_hours": {
                    "type": "integer",
                    "title": "冷却时间(小时)",
                    "description": "对同一发件人再次自动回复的间隔时间",
                    "default": 24,
                    "minimum": 1,
                    "maximum": 168
                }
            }
        },
        "default_config": {
            "reply_once_per_sender": True,
            "cooldown_hours": 24
        }
    }
}


# ==================== 系统工作流更新 ====================

def update_system_workflow_configs(db: Session, dry_run: bool = False):
    """更新系统工作流的配置项"""
    print("=" * 60)
    print("更新系统工作流配置项")
    print("=" * 60)

    updated = 0
    skipped = 0

    workflows = db.query(SystemWorkflow).all()
    print(f"\n找到 {len(workflows)} 个系统工作流\n")

    for wf in workflows:
        if wf.code in SYSTEM_WORKFLOW_CONFIGS:
            config = SYSTEM_WORKFLOW_CONFIGS[wf.code]

            # 检查是否需要更新
            needs_update = (
                wf.config_schema != config["config_schema"] or
                wf.default_config != config["default_config"]
            )

            if needs_update:
                wf.config_schema = config["config_schema"]
                wf.default_config = config["default_config"]
                print(f"[更新] {wf.name} ({wf.code})")
                print(f"       配置项: {list(config['config_schema']['properties'].keys())}")
                updated += 1
            else:
                print(f"[跳过] {wf.name} ({wf.code}) - 配置已是最新")
                skipped += 1
        else:
            print(f"[跳过] {wf.name} ({wf.code}) - 无预设配置")
            skipped += 1

    if updated > 0 and not dry_run:
        db.commit()
        print(f"\n已提交更改")

    print(f"\n" + "=" * 60)
    print(f"系统工作流完成! 更新: {updated}, 跳过: {skipped}")
    print("=" * 60)

    return updated


# ==================== 用户工作流更新 ====================

def get_node_type_configs(db: Session) -> dict:
    """获取所有节点类型的配置schema"""
    node_types = db.query(NodeType).filter(NodeType.is_active == True).all()
    return {nt.code: nt.config_schema for nt in node_types if nt.config_schema}


def extract_workflow_config_from_nodes(workflow: Workflow, nodes: list, node_type_configs: dict) -> tuple:
    """
    从工作流节点中提取配置项
    返回 (config_schema, default_config)
    """
    properties = {}
    defaults = {}

    for node in nodes:
        node_subtype = node.node_subtype
        node_config = node.config or {}

        # 获取节点类型的配置schema
        if node_subtype not in node_type_configs:
            continue

        type_schema = node_type_configs[node_subtype]
        if not type_schema or 'properties' not in type_schema:
            continue

        # 检查每个配置项是否可提升到工作流级别
        for key, prop_schema in type_schema.get('properties', {}).items():
            # 如果配置项标记为 promotable，或者是常用配置项，则提升到工作流级别
            if prop_schema.get('promotable', False):
                # 生成唯一的配置键名 (节点ID + 配置项名)
                config_key = f"{node.node_id}_{key}"

                # 复制配置项定义
                new_prop = dict(prop_schema)
                new_prop['title'] = f"{node.name or node_subtype}: {prop_schema.get('title', key)}"
                new_prop['_source_node'] = node.node_id
                new_prop['_source_key'] = key

                properties[config_key] = new_prop

                # 获取默认值
                if key in node_config:
                    defaults[config_key] = node_config[key]
                elif 'default' in prop_schema:
                    defaults[config_key] = prop_schema['default']

    if not properties:
        return None, None

    config_schema = {
        "type": "object",
        "properties": properties
    }

    return config_schema, defaults


def update_user_workflow_configs(db: Session, dry_run: bool = False):
    """更新用户工作流的配置项（基于节点自动提取）"""
    print("\n" + "=" * 60)
    print("更新用户工作流配置项")
    print("=" * 60)

    # 获取节点类型配置
    node_type_configs = get_node_type_configs(db)
    print(f"\n加载了 {len(node_type_configs)} 个节点类型配置\n")

    updated = 0
    skipped = 0
    no_nodes = 0

    workflows = db.query(Workflow).all()
    print(f"找到 {len(workflows)} 个用户工作流\n")

    for wf in workflows:
        # 获取工作流的节点
        nodes = db.query(WorkflowNode).filter(WorkflowNode.workflow_id == wf.id).all()

        if not nodes:
            print(f"[跳过] {wf.name} (ID:{wf.id}) - 无节点")
            no_nodes += 1
            continue

        # 如果工作流已有配置，保留现有配置
        if wf.config_schema and wf.config_schema.get('properties'):
            print(f"[保留] {wf.name} (ID:{wf.id}) - 已有 {len(wf.config_schema['properties'])} 个配置项")
            skipped += 1
            continue

        # 尝试从节点提取配置
        config_schema, default_config = extract_workflow_config_from_nodes(wf, nodes, node_type_configs)

        if config_schema:
            wf.config_schema = config_schema
            wf.default_config = default_config or {}
            if not wf.config:
                wf.config = {}
            print(f"[更新] {wf.name} (ID:{wf.id})")
            print(f"       提取了 {len(config_schema['properties'])} 个配置项")
            updated += 1
        else:
            # 初始化为空配置结构
            if wf.config_schema is None:
                wf.config_schema = {"type": "object", "properties": {}}
            if wf.default_config is None:
                wf.default_config = {}
            if wf.config is None:
                wf.config = {}
            print(f"[初始化] {wf.name} (ID:{wf.id}) - 初始化空配置结构")
            updated += 1

    if updated > 0 and not dry_run:
        db.commit()
        print(f"\n已提交更改")

    print(f"\n" + "=" * 60)
    print(f"用户工作流完成! 更新: {updated}, 保留: {skipped}, 无节点: {no_nodes}")
    print("=" * 60)

    return updated


# ==================== 列表功能 ====================

def list_workflow_configs(db: Session):
    """列出所有工作流的配置状态"""
    print("\n" + "=" * 60)
    print("系统工作流配置状态")
    print("=" * 60 + "\n")

    workflows = db.query(SystemWorkflow).order_by(SystemWorkflow.category, SystemWorkflow.id).all()

    current_category = None
    for wf in workflows:
        if wf.category != current_category:
            current_category = wf.category
            print(f"\n--- {current_category.upper()} ---")

        has_schema = "有" if wf.config_schema else "无"
        has_config = "有" if wf.default_config else "无"
        config_count = len(wf.config_schema.get("properties", {})) if wf.config_schema else 0

        print(f"  {wf.name} ({wf.code})")
        print(f"    Schema: {has_schema} | 默认配置: {has_config} | 配置项数: {config_count}")

        if wf.config_schema and wf.config_schema.get("properties"):
            for key, prop in wf.config_schema["properties"].items():
                default_val = wf.default_config.get(key, "-") if wf.default_config else "-"
                print(f"      - {prop.get('title', key)}: {default_val}")

    # 用户工作流
    print("\n" + "=" * 60)
    print("用户工作流配置状态")
    print("=" * 60 + "\n")

    user_workflows = db.query(Workflow).order_by(Workflow.owner_id, Workflow.id).all()

    for wf in user_workflows:
        has_schema = "有" if wf.config_schema and wf.config_schema.get("properties") else "无"
        has_config = "有" if wf.default_config else "无"
        config_count = len(wf.config_schema.get("properties", {})) if wf.config_schema else 0

        nodes_count = db.query(WorkflowNode).filter(WorkflowNode.workflow_id == wf.id).count()

        print(f"  [{wf.status}] {wf.name} (ID:{wf.id}, 节点数:{nodes_count})")
        print(f"    Schema: {has_schema} | 默认配置: {has_config} | 配置项数: {config_count}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="更新工作流配置项")
    parser.add_argument("--list", "-l", action="store_true", help="列出当前配置状态")
    parser.add_argument("--update", "-u", action="store_true", help="执行更新")
    parser.add_argument("--dry-run", "-d", action="store_true", help="只显示将要做的更改，不实际执行")
    parser.add_argument("--system-only", "-s", action="store_true", help="仅更新系统工作流")
    parser.add_argument("--user-only", "-p", action="store_true", help="仅更新用户工作流")

    args = parser.parse_args()

    db = SessionLocal()

    try:
        if args.list:
            list_workflow_configs(db)
        elif args.update or args.dry_run:
            if args.dry_run:
                print("\n[DRY RUN 模式 - 不会实际修改数据库]\n")

            total_updated = 0

            # 更新系统工作流
            if not args.user_only:
                total_updated += update_system_workflow_configs(db, dry_run=args.dry_run)

            # 更新用户工作流
            if not args.system_only:
                total_updated += update_user_workflow_configs(db, dry_run=args.dry_run)

            if args.dry_run:
                db.rollback()
                print("\n[DRY RUN 完成 - 已回滚所有更改]")
            else:
                print(f"\n总计更新了 {total_updated} 个工作流")
        else:
            # 默认显示帮助
            parser.print_help()
            print("\n示例:")
            print("  python update_workflow_configs.py --list        # 查看当前状态")
            print("  python update_workflow_configs.py --dry-run     # 预览更改")
            print("  python update_workflow_configs.py --update      # 执行更新（全部）")
            print("  python update_workflow_configs.py --update -s   # 仅更新系统工作流")
            print("  python update_workflow_configs.py --update -p   # 仅更新用户工作流")
    finally:
        db.close()


if __name__ == "__main__":
    main()
