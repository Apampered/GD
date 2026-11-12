# app/api/v1/admin.py
from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/")
async def admin_panel():
    return {"message": "后台管理功能开发中"}