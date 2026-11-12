import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",      # 注意是字符串！
        host="0.0.0.0",
        port=8000,
        workers=2,
        log_level="info"
    )