# app/services/inpaint_service.py
from fastapi import UploadFile
from PIL import Image
import io
from fastapi.concurrency import run_in_threadpool
import logging

from app.utils.image_utils import save_uploaded_image, save_output_image, get_output_url, get_upload_url
from app.workflow.inpainting import inpainting_workflow   # 你的底层脚本

logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000"

async def process_inpainting(
    original_image: UploadFile,
    mask_image: UploadFile,
    prompt: str = "",
    strength: float = 0.75,
    seed: int = None,
):
    try:
        # 1. 读取文件
        orig_bytes = await original_image.read()
        mask_bytes = await mask_image.read()

        # 2. 保存原始图片和遮罩
        orig_path = save_uploaded_image(orig_bytes)
        mask_path = save_uploaded_image(mask_bytes)

        orig_url = f"{BASE_URL}{get_upload_url(orig_path)}"
        mask_url = f"{BASE_URL}{get_upload_url(mask_path)}"
        # 3. 调用底层 inpainting 函数
        output_path = await run_in_threadpool(
            inpainting_workflow,
            original_image=orig_url,
            mask_image=mask_url,
            prompt=prompt,
            strength=strength,
            seed=seed
        )

        return {
            "success": True,
            "original_path": str(orig_path),
            "mask_path": str(mask_path),
            "output_url": f"{BASE_URL}{get_output_url(output_path)}",
            "prompt": prompt,
            "strength": strength
        }

    except Exception as e:
        logger.error(f"Inpainting 处理异常: {e}")
        raise