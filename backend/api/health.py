"""
健康检查 API
用于容器健康检查和负载均衡器探测
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from db.database import get_db

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    健康检查端点
    
    检查项：
    1. API 服务是否运行
    2. 数据库连接是否正常
    
    Returns:
        dict: 健康状态信息
    """
    try:
        # 测试数据库连接
        db.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "service": "talentmail-backend",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "talentmail-backend",
            "database": "disconnected",
            "error": str(e)
        }


@router.get("/readiness")
async def readiness_check(db: Session = Depends(get_db)):
    """
    就绪检查端点
    
    检查服务是否准备好接收流量
    
    Returns:
        dict: 就绪状态信息
    """
    try:
        # 测试数据库连接
        db.execute(text("SELECT 1"))
        
        return {
            "status": "ready",
            "service": "talentmail-backend"
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "service": "talentmail-backend",
            "error": str(e)
        }


@router.get("/liveness")
async def liveness_check():
    """
    存活检查端点
    
    检查服务进程是否存活
    
    Returns:
        dict: 存活状态信息
    """
    return {
        "status": "alive",
        "service": "talentmail-backend"
    }