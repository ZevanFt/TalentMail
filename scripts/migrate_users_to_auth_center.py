#!/usr/bin/env python3
"""把 TalentMail 侧尚未绑定 SSO 的用户批量迁到 Auth-Center，并回写 sso_user_id。

默认 dry-run；加 --apply 才会真正创建/绑定。

用法（仓库根目录）:
  set AUTH_CENTER_ADMIN_PASSWORD=...
  python scripts/migrate_users_to_auth_center.py
  python scripts/migrate_users_to_auth_center.py --apply
  python scripts/migrate_users_to_auth_center.py --apply --limit 20
  python scripts/migrate_users_to_auth_center.py --apply --emails a@x.com,b@x.com

环境变量:
  AUTH_CENTER_BASE_URL          默认 http://127.0.0.1:8000
  AUTH_CENTER_ADMIN_USER        默认从 Auth-Center 读，或 admin@talenting.vip
  AUTH_CENTER_ADMIN_PASSWORD    必填
  TALENTMAIL_DB_CONTAINER       默认 talentmail-db-1
  TALENTMAIL_DB_USER            默认 talentmail
  TALENTMAIL_DB_NAME            默认 talentmail
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import secrets
import string
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Any

BASE = os.getenv("AUTH_CENTER_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
ADMIN_USER = os.getenv("AUTH_CENTER_ADMIN_USER", "admin@talenting.vip")
ADMIN_PASS = os.getenv("AUTH_CENTER_ADMIN_PASSWORD", "")
DB_CONTAINER = os.getenv("TALENTMAIL_DB_CONTAINER", "talentmail-db-1")
DB_USER = os.getenv("TALENTMAIL_DB_USER", "talentmail")
DB_NAME = os.getenv("TALENTMAIL_DB_NAME", "talentmail")


def psql(sql: str, tuples_only: bool = True) -> str:
    cmd = ["docker", "exec", DB_CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-A"]
    if tuples_only:
        cmd.append("-t")
    cmd.extend(["-c", sql])
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"psql failed: {result.stderr.strip()}")
    return result.stdout


def random_password(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    # 保证至少 1 字母 + 1 数字
    pwd = [secrets.choice(string.ascii_letters), secrets.choice(string.digits)]
    pwd += [secrets.choice(alphabet) for _ in range(length - 2)]
    secrets.SystemRandom().shuffle(pwd)
    return "".join(pwd)


class AuthCenterClient:
    def __init__(self, base: str):
        self.base = base
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj)
        )
        self.csrf = ""

    def _headers(self, extra: dict | None = None) -> dict:
        h = {"Content-Type": "application/json"}
        if self.csrf:
            h["X-CSRF-Token"] = self.csrf
        if extra:
            h.update(extra)
        return h

    def login(self, username: str, password: str) -> dict:
        body = self._request("POST", "/api/auth/login", {"username": username, "password": password})
        self.csrf = next((c.value for c in self.cj if c.name == "csrf_token"), "")
        return body

    def _request(self, method: str, path: str, data: dict | None = None) -> Any:
        req = urllib.request.Request(
            self.base + path,
            data=json.dumps(data).encode() if data is not None else None,
            method=method,
            headers=self._headers(),
        )
        try:
            with self.opener.open(req, timeout=30) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(f"{method} {path} -> {e.code}: {detail}") from e

    def list_users(self) -> list[dict]:
        summary = self._request("GET", "/api/admin/summary")
        return summary.get("users") or []

    def create_user(self, username: str, display_name: str, password: str) -> dict:
        return self._request(
            "POST",
            "/api/admin/users",
            {
                "username": username,
                "display_name": display_name,
                "password": password,
                "is_admin": False,
            },
        )


def load_mail_users(only_missing: bool = True, emails: list[str] | None = None, limit: int | None = None) -> list[dict]:
    where = ["1=1"]
    if only_missing:
        where.append("(sso_user_id IS NULL OR sso_user_id = '')")
    if emails:
        quoted = ", ".join("'" + e.replace("'", "''") + "'" for e in emails)
        where.append(f"lower(email) IN ({quoted})")
    sql = (
        "SELECT id, email, COALESCE(display_name, ''), COALESCE(role, 'user') "
        "FROM users WHERE " + " AND ".join(where) + " ORDER BY id"
    )
    if limit:
        sql += f" LIMIT {int(limit)}"
    out = psql(sql)
    users = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|")
        if len(parts) < 4:
            continue
        users.append({
            "id": int(parts[0]),
            "email": parts[1],
            "display_name": parts[2],
            "role": parts[3],
        })
    return users


def bind_sso_user(mail_user_id: int, sso_user_id: str) -> None:
    safe = sso_user_id.replace("'", "''")
    psql(f"UPDATE users SET sso_user_id = '{safe}' WHERE id = {int(mail_user_id)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate TalentMail users to Auth-Center")
    parser.add_argument("--apply", action="store_true", help="真正执行创建与绑定（默认 dry-run）")
    parser.add_argument("--limit", type=int, default=None, help="最多处理 N 个用户")
    parser.add_argument("--emails", type=str, default="", help="仅处理逗号分隔的邮箱列表")
    args = parser.parse_args()

    if not ADMIN_PASS:
        print("错误：请设置 AUTH_CENTER_ADMIN_PASSWORD", file=sys.stderr)
        return 2

    emails = [e.strip().lower() for e in args.emails.split(",") if e.strip()]
    mail_users = load_mail_users(only_missing=True, emails=emails or None, limit=args.limit)

    print(f"模式: {'APPLY' if args.apply else 'DRY-RUN'}")
    print(f"TalentMail 待处理用户: {len(mail_users)}")

    client = AuthCenterClient(BASE)
    try:
        login_body = client.login(ADMIN_USER, ADMIN_PASS)
        print(f"Auth-Center 登录: {login_body.get('user', {}).get('username', ADMIN_USER)}")
    except Exception as e:
        print(f"Auth-Center 登录失败: {e}", file=sys.stderr)
        return 1

    existing = {u["username"].lower(): u for u in client.list_users()}
    print(f"Auth-Center 已有用户: {len(existing)}")

    created = linked = skipped = failed = 0
    for u in mail_users:
        email = u["email"].lower()
        display = u["display_name"] or email.split("@")[0]
        if email in existing:
            sso_id = existing[email]["id"]
            action = "link"
        else:
            action = "create"
            sso_id = None

        if action == "create":
            pwd = random_password()
            if not args.apply:
                print(f"  [dry-run] 将创建 {email} (display={display})")
                created += 1
                continue
            try:
                created_user = client.create_user(email, display, pwd)
                sso_id = created_user["id"]
                existing[email] = created_user
                print(f"  + 创建 {email} -> sso_id={sso_id}")
                created += 1
            except Exception as e:
                print(f"  ! 创建失败 {email}: {e}", file=sys.stderr)
                failed += 1
                continue
        else:
            if not args.apply:
                print(f"  [dry-run] 将关联已有 {email} -> sso_id={sso_id}")
                linked += 1
                continue

        try:
            bind_sso_user(u["id"], str(sso_id))
            print(f"  = 绑定 mail_id={u['id']} {email} -> {sso_id}")
            linked += 1
        except Exception as e:
            print(f"  ! 绑定失败 {email}: {e}", file=sys.stderr)
            failed += 1

    print("---")
    print(f"新建: {created}  绑定: {linked}  失败: {failed}  跳过: {skipped}")
    if not args.apply:
        print("以上为 dry-run。确认无误后加 --apply 执行。")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
