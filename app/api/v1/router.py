# app/api/v1/router.py
from fastapi import APIRouter
from . import generation, history, admin, inpainting, changebackground, stylerepainting, t2i   # 导入各个模块的 router

# 创建 v1 主路由（推荐加上 prefix 和 tags，便于 Swagger 分组）
api_v1_router = APIRouter(
    prefix="/api/v1",
    tags=["v1"]
)

# 注册各个子路由（按模块拆分，结构清晰）
api_v1_router.include_router(generation.router)
api_v1_router.include_router(history.router)
api_v1_router.include_router(admin.router)
api_v1_router.include_router(inpainting.router)
# api_v1_router.include_router(changebackground.router)
# api_v1_router.include_router(stylerepainting.router)
# api_v1_router.include_router(t2i.router)
