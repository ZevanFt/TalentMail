"""
SpamAssassin 训练执行器
"""
from __future__ import annotations

import io
import logging
import os
import tarfile
import uuid
from datetime import datetime, timezone
from email.utils import format_datetime
from html import unescape
import re

from docker.errors import APIError, NotFound

from core.mailserver_sync import get_docker_client

logger = logging.getLogger(__name__)

MAILSERVER_CONTAINER_NAME = os.getenv("MAILSERVER_CONTAINER_NAME", "talentmail-mailserver-1")
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _html_to_text(html: str) -> str:
    text = _HTML_TAG_RE.sub(" ", html or "")
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _build_eml_content(report) -> bytes:
    email_obj = getattr(report, "email", None)
    subject = getattr(email_obj, "subject", None) or "(no subject)"
    sender = getattr(email_obj, "sender", None) or "unknown@example.invalid"
    recipients = getattr(email_obj, "recipients", None) or "unknown@example.invalid"
    body_text = getattr(email_obj, "body_text", None) or ""
    body_html = getattr(email_obj, "body_html", None) or ""

    if not body_text and body_html:
        body_text = _html_to_text(body_html)
    if not body_text:
        body_text = "(empty body)"

    now = format_datetime(datetime.now(timezone.utc))
    eml = (
        f"From: {sender}\n"
        f"To: {recipients}\n"
        f"Subject: {subject}\n"
        f"Date: {now}\n"
        "MIME-Version: 1.0\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "Content-Transfer-Encoding: 8bit\n"
        "\n"
        f"{body_text}\n"
    )
    return eml.encode("utf-8", errors="replace")


def _build_tar_payload(file_name: str, content: bytes) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        info = tarfile.TarInfo(name=file_name)
        info.size = len(content)
        info.mtime = int(datetime.now(tz=timezone.utc).timestamp())
        tar.addfile(info, io.BytesIO(content))
    buf.seek(0)
    return buf.read()


def train_report_with_spamassassin(report, report_type: str) -> None:
    if report_type not in {"spam", "ham"}:
        raise ValueError(f"Invalid report_type: {report_type}")

    client = get_docker_client()
    if client is None:
        raise RuntimeError("Docker client unavailable")

    try:
        container = client.containers.get(MAILSERVER_CONTAINER_NAME)
    except NotFound as exc:
        raise RuntimeError(f"Mailserver container not found: {MAILSERVER_CONTAINER_NAME}") from exc
    except APIError as exc:
        raise RuntimeError(f"Failed to access mailserver container: {exc}") from exc

    container_file_name = f"tm-sa-learn-{report.id}-{uuid.uuid4().hex}.eml"
    container_file_path = f"/tmp/{container_file_name}"
    command_flag = "--spam" if report_type == "spam" else "--ham"

    eml_content = _build_eml_content(report)
    tar_payload = _build_tar_payload(container_file_name, eml_content)

    if not container.put_archive("/tmp", tar_payload):
        raise RuntimeError("Failed to upload EML payload into mailserver container")

    try:
        result = container.exec_run(["sa-learn", command_flag, container_file_path], demux=True)
        if result.exit_code != 0:
            stderr = result.output[1].decode("utf-8", errors="replace") if result.output and result.output[1] else ""
            stdout = result.output[0].decode("utf-8", errors="replace") if result.output and result.output[0] else ""
            raise RuntimeError(f"sa-learn failed(exit={result.exit_code}): {stderr or stdout or 'unknown error'}")
    finally:
        cleanup = container.exec_run(["rm", "-f", container_file_path], demux=True)
        if cleanup.exit_code != 0:
            logger.warning(
                "spamassassin_cleanup_failed",
                extra={"report_id": report.id, "path": container_file_path},
            )
