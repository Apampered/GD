# app/main.py   —— 极简调试版（直接复制替换）
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Sketch2Image AI图像生成平台",
    description="毕设调试版",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},  # 可选，减少加载
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.v1.router import api_v1_router
app.include_router(api_v1_router)

for dir_name in ["outputs", "uploads", "static"]:
    if os.path.exists(dir_name):
        app.mount(f"/{dir_name}", StaticFiles(directory=dir_name), name=dir_name)

# if os.path.exists("frontend/dist"):
#     app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
#     print("✅ Vue 前端已挂载（打包模式）")
# else:
#     print("⚠️ 未找到 frontend/dist 文件夹，请先执行 npm run build")

@app.get("/")
async def root():
    return {
        "message": "后端服务已正常启动！",
        "docs": "http://127.0.0.1:8000/docs",
        "status": "ok"
    }

if __name__ == "__main__":
    import uvicorn
    # E:\GD > uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, workers=2, log_level="info")