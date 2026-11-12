# app/api/v1/generation.py
from fastapi import APIRouter, UploadFile, File, Form, Depends, BackgroundTasks
from ...schemas.generation import GenerationResponse
from ...services.generation_service import process_sketch_generation
import logging
import traceback

router = APIRouter(prefix="/generation", tags=["AI Generation"])
logger = logging.getLogger(__name__)
@router.post("/sketch", response_model=GenerationResponse)
async def generate_sketch(
    sketch: UploadFile = File(...),
    style: str = Form("cartoon"),
    strength: float = Form(0.75),
    seed: int = Form(None),
    # background_tasks: BackgroundTasks   # 后面用于异步
):
    try:
        logger.info(f"收到生成请求 - 文件: {sketch.filename}, style: {style}, strength: {strength}")

        # 这里必须加 await！因为 process_sketch_generation 很可能是 async 的
        result = await process_sketch_generation(
            sketch_file=sketch,
            style=style,
            strength=strength,
            seed=seed
        )

        logger.info("生成成功，返回结果")
        return GenerationResponse(code=200, msg="生成成功", data=result)

    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"生成失败: {str(e)}\n{error_detail}")
        return GenerationResponse(
            code=500,
            msg=f"生成失败: {str(e)}",
            data={"error": str(e), "traceback": error_detail}
        )
