"""图片代理 API — 防止远程图片直接加载导致隐私泄露"""
import requests as req_lib
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from api.deps import get_current_user
from db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proxy", tags=["proxy"])

# 允许代理的内容类型白名单
ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "image/svg+xml", "image/bmp", "image/ico", "image/x-icon",
}

# 最大代理文件大小 (5MB)
MAX_PROXY_SIZE = 5 * 1024 * 1024


@router.get("/image")
def proxy_image(
    url: str = Query(..., description="要代理的图片 URL"),
    user: User = Depends(get_current_user),
):
    """代理远程图片，防止邮件中的图片直接暴露用户 IP"""
    if not url.startswith(("http://", "https://")):
        raise HTTPException(400, "仅支持 HTTP/HTTPS URL")

    try:
        session = req_lib.Session()
        session.max_redirects = 3
        resp = session.get(
            url,
            timeout=10,
            allow_redirects=True,
            headers={"User-Agent": "TalentMail-ImageProxy/1.0"},
            stream=True,
        )

        if resp.status_code != 200:
            raise HTTPException(502, f"远程服务器返回 {resp.status_code}")

        content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(400, f"不支持的内容类型: {content_type}")

        # 流式读取，限制大小
        content = resp.content
        if len(content) > MAX_PROXY_SIZE:
            raise HTTPException(413, "图片过大")

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
