"""TalentMail Open API 轻量客户端。

用法:
    from talentmail_client import TalentMailClient

    client = TalentMailClient(base_url="https://mail.example.com/api", api_key="tm_xxx")
    mailbox = client.create_temp_mailbox(prefix="e2e", purpose="signup")
    code = client.wait_for_code(mailbox["id"], timeout=60)
"""
from __future__ import annotations

import time
from typing import Any, Optional

import requests


class TalentMailError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(f"[{status_code}] {detail}")
        self.status_code = status_code
        self.detail = detail


class TalentMailClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 15.0,
        session: Optional[requests.Session] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[dict] = None,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        idempotency_key: Optional[str] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        req_headers = dict(headers or {})
        if idempotency_key:
            req_headers["Idempotency-Key"] = idempotency_key
        resp = self.session.request(
            method,
            url,
            json=json,
            params=params,
            headers=req_headers or None,
            timeout=self.timeout,
        )
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise TalentMailError(resp.status_code, str(detail))
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    # ---- temp mailboxes ----
    def create_temp_mailbox(
        self,
        prefix: Optional[str] = None,
        purpose: Optional[str] = None,
        auto_verify_codes: bool = True,
        idempotency_key: Optional[str] = None,
    ) -> dict:
        payload: dict[str, Any] = {"auto_verify_codes": auto_verify_codes}
        if prefix:
            payload["prefix"] = prefix
        if purpose:
            payload["purpose"] = purpose
        return self._request(
            "POST",
            "/automation/temp-mailboxes",
            json=payload,
            idempotency_key=idempotency_key,
        )

    def list_temp_mailboxes(self, include_purged: bool = False) -> list[dict]:
        return self._request(
            "GET",
            "/automation/temp-mailboxes",
            params={"include_purged": include_purged},
        )

    def get_emails(
        self,
        mailbox_id: int,
        include_body: bool = False,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        return self._request(
            "GET",
            f"/automation/temp-mailboxes/{mailbox_id}/emails",
            params={
                "include_body": include_body,
                "page": page,
                "limit": limit,
            },
        )

    def get_latest_code(
        self,
        mailbox_id: int,
        within_minutes: int = 5,
        sender_contains: Optional[str] = None,
        subject_contains: Optional[str] = None,
        unread_only: bool = False,
    ) -> Optional[dict]:
        params: dict[str, Any] = {
            "within_minutes": within_minutes,
            "unread_only": unread_only,
        }
        if sender_contains:
            params["sender_contains"] = sender_contains
        if subject_contains:
            params["subject_contains"] = subject_contains
        return self._request(
            "GET",
            f"/automation/temp-mailboxes/{mailbox_id}/codes/latest",
            params=params,
        )

    def wait_for_code(
        self,
        mailbox_id: int,
        timeout: float = 60.0,
        interval: float = 3.0,
        within_minutes: int = 5,
        **filters: Any,
    ) -> str:
        """轮询直到拿到验证码或超时。返回 code 字符串。"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            result = self.get_latest_code(
                mailbox_id,
                within_minutes=within_minutes,
                **filters,
            )
            if result and result.get("code"):
                return result["code"]
            time.sleep(interval)
        raise TimeoutError(f"在 {timeout}s 内未获取到验证码 (mailbox_id={mailbox_id})")

    def extend_mailbox(self, mailbox_id: int, hours: int = 24) -> dict:
        return self._request(
            "POST",
            f"/automation/temp-mailboxes/{mailbox_id}/extend",
            json={"hours": hours},
        )

    def restore_mailbox(self, mailbox_id: int) -> dict:
        return self._request(
            "POST",
            f"/automation/temp-mailboxes/{mailbox_id}/restore",
        )
