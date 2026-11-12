# app/services/generation_service.py
from PIL import Image
import io
from pathlib import Path
from fastapi import UploadFile
from app.workflow.generate import generate_from_sketch  # 直接导入你的函数
from fastapi.concurrency import run_in_threadpool
from app.utils.image_utils import save_uploaded_image, save_output_image, get_output_url
import logging

logger = logging.getLogger(__name__)

async def process_sketch_generation(
        sketch_file: UploadFile,
        style: str,
        strength: float,
        seed: int = None,
        # 其他参数...
) -> dict:
    try:
        contents = await sketch_file.read()
        upload_path = save_uploaded_image(contents)
        output_path = await run_in_threadpool(
            generate_from_sketch,
            sketch_image=upload_path,
            style=style,
            strength=strength,
            seed=seed
        )

        # 4. 返回规范的字典
        return {
            "success": True,
            "input_path": str(upload_path),
            "output_path": str(output_path),
            "output_url": get_output_url(output_path),
            "style": style,
            "seed": seed,
            "message": "图像生成成功"
        }

    except Exception as e:
        logger.error(f"生成过程异常: {str(e)}")
        raise