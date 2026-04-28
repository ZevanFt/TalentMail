"""图片代理 API — 防止远程图片直接加载导致隐私泄露"""
import ipaddress
import socket
from urllib.parse import urlparse

import requests as req_lib
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from api.deps import get_current_user
from db.models.user import User
from utils.rate_limit import SlidingWindowLimiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proxy", tags=["proxy"])
_proxy_limiter = SlidingWindowLimiter(max_attempts=30, window_seconds=60)

# 允许代理的内容类型白名单（SVG 已移除 — 可携带 <script> 导致 XSS）
ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "image/bmp", "image/ico", "image/x-icon",
}

# 最大代理文件大小 (5MB)
MAX_PROXY_SIZE = 5 * 1024 * 1024

# 最大重定向次数
MAX_REDIRECTS = 3

# SSRF 防护：禁止访问的内网 IP 段
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),   # Carrier-grade NAT
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),          # Unique local
    ipaddress.ip_network("fe80::/10"),         # Link-local
]


def _is_ip_blocked(ip_str: str) -> bool:
    """检查 IP 地址是否属于内网/保留网段"""
    try:
        addr = ipaddress.ip_address(ip_str)
        for net in _BLOCKED_NETWORKS:
            if addr in net:
                return True
        return False
    except ValueError:
        return True  # 解析失败视为不安全


def _validate_url_ssrf(url: str) -> None:
    """DNS 解析 URL 的主机名，并验证解析出的 IP 不在内网段"""
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(400, "无效的 URL")

    # 直接 IP 检查
    try:
        addr = ipaddress.ip_address(hostname)
        if _is_ip_blocked(str(addr)):
            logger.warning(f"SSRF 拦截: 目标 IP {hostname} 属于内网/保留网段")
            raise HTTPException(403, "禁止访问内部网络地址")
        return
    except ValueError:
        pass  # 不是 IP，是域名，继续 DNS 解析

    # DNS 解析检查
    try:
        addrinfos = socket.getaddrinfo(hostname, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise HTTPException(400, f"无法解析主机名: {hostname}")

    for family, _type, _proto, _canonname, sockaddr in addrinfos:
        ip_str = sockaddr[0]
        if _is_ip_blocked(ip_str):
            logger.warning(f"SSRF 拦截: 域名 {hostname} 解析到内网 IP {ip_str}")
            raise HTTPException(403, "禁止访问内部网络地址")


@router.get("/image")
def proxy_image(
    url: str = Query(..., description="要代理的图片 URL"),
    user: User = Depends(get_current_user),
):
    """代理远程图片，防止邮件中的图片直接暴露用户 IP"""
    if not _proxy_limiter.allow(f"proxy:{user.id}"):
        raise HTTPException(429, "请求过于频繁，请稍后再试")
    if not url.startswith(("http://", "https://")):
        raise HTTPException(400, "仅支持 HTTP/HTTPS URL")

    # SSRF 防护：在发起请求前检查目标 IP
    _validate_url_ssrf(url)

    try:
        session = req_lib.Session()

        # 手动跟随重定向，每一跳都做 SSRF 检查（防止 302 跳转到内网）
        current_url = url
        resp = None
        for hop in range(MAX_REDIRECTS + 1):
            resp = session.get(
                current_url,
                timeout=10,
                allow_redirects=False,
                headers={"User-Agent": "TalentMail-ImageProxy/1.0"},
                stream=True,
            )

            if resp.status_code in (301, 302, 303, 307, 308):
                redirect_url = resp.headers.get("Location")
                if not redirect_url:
                    raise HTTPException(502, "重定向缺少 Location 头")
                # 处理相对路径重定向
                if redirect_url.startswith("/"):
                    parsed = urlparse(current_url)
                    redirect_url = f"{parsed.scheme}://{parsed.netloc}{redirect_url}"
                if not redirect_url.startswith(("http://", "https://")):
                    raise HTTPException(400, "重定向目标不是合法 HTTP URL")
                # 对重定向目标重新做 SSRF 检查
                _validate_url_ssrf(redirect_url)
                current_url = redirect_url
                resp.close()
                continue

            break  # 非重定向，正常响应
        else:
            raise HTTPException(502, "重定向次数过多")

        if resp.status_code != 200:
            raise HTTPException(502, f"远程服务器返回 {resp.status_code}")

        content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
        if content_type not in ALLOWED_CONTENT_TYPES:
            resp.close()
            raise HTTPException(400, f"不支持的内容类型: {content_type}")

        # 流式读取，边读边检查大小（不会一次性吃满内存）
        chunks = []
        total_size = 0
        for chunk in resp.iter_content(chunk_size=65536):
            total_size += len(chunk)
            if total_size > MAX_PROXY_SIZE:
                resp.close()
                raise HTTPException(413, "图片过大")
            chunks.append(chunk)
        resp.close()

        content = b"".join(chunks)

        return Response(
            content=content,
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=86400",
                "X-Content-Type-Options": "nosniff",
            },
        )

    except req_lib.Timeout:
        raise HTTPException(504, "图片加载超时")
    except req_lib.RequestException as e:
        logger.warning(f"图片代理请求失败: {url} - {e}")
        raise HTTPException(502, "图片加载失败")
