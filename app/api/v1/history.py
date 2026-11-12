# app/api/v1/history.py
from fastapi import APIRouter

router = APIRouter(prefix="/history", tags=["History"])

@router.get("/")
async def get_history():
    return {"message": "生成历史功能开发中"}