#!/usr/bin/env python3
"""完整 E2E：创建临时邮箱 → 等验证码 → （你在这里调用第三方注册）。

环境变量:
  TALENTMAIL_BASE_URL  例如 https://mail.example.com/api
  TALENTMAIL_API_KEY   tm_xxx
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from talentmail_client import TalentMailClient, TalentMailError  # noqa: E402


def main() -> None:
    base_url = os.environ.get("TALENTMAIL_BASE_URL", "https://mail.example.com/api")
    api_key = os.environ.get("TALENTMAIL_API_KEY")
    if not api_key:
        print("请设置 TALENTMAIL_API_KEY", file=sys.stderr)
        sys.exit(1)

    client = TalentMailClient(base_url=base_url, api_key=api_key)

    try:
        mailbox = client.create_temp_mailbox(
            prefix="signup-demo",
            purpose="Python SDK demo",
            idempotency_key="demo-python-signup-001",
        )
        print(f"创建成功: {mailbox['email']} (id={mailbox['id']})")

        # 在这里把 mailbox['email'] 填到第三方注册表单
        print("请用该邮箱完成第三方注册，等待验证码...")

        code = client.wait_for_code(
            mailbox["id"],
            timeout=90,
            interval=3,
            within_minutes=5,
        )
        print(f"验证码: {code}")

        # 在这里提交验证码完成注册
        # third_party.verify(email=mailbox["email"], code=code)

    except TalentMailError as e:
        print(f"API 错误: {e}", file=sys.stderr)
        sys.exit(2)
    except TimeoutError as e:
        print(f"超时: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
