# app/api/v1/inpaint.py
from fastapi import APIRouter, UploadFile, File, Form
from ...schemas.generation import GenerationResponse
from ...services.inpainting_service import process_inpainting
import logging

router = APIRouter(prefix="/generation", tags=["Inpainting"])

logger = logging.getLogger(__name__)

@router.post("/inpainting", response_model=GenerationResponse)
async def inpainting(
    image: UploadFile = File(..., description="原始图片"),
    mask: UploadFile = File(..., description="遮罩图片（白色区域为重绘部分）"),
    prompt: str = Form("", description="可选提示词"),
    strength: float = Form(0.75, ge=0.0, le=1.0),
    seed: int = Form(None)
):
    try:
        logger.info(f"Inpainting 请求 - image: {image.filename}, mask: {mask.filename}")

        result = await process_inpainting(
            original_image=image,
            mask_image=mask,
            prompt=prompt,
            strength=strength,
            seed=seed
        )

        return GenerationResponse(
            code=200,
            msg="局部重绘成功",
            data=result
        )

    except Exception as e:
        logger.error(f"Inpaint 失败: {str(e)}")
        return GenerationResponse(
            code=500,
            msg=f"生成失败: {str(e)}",
            data=None
        )