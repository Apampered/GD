from datetime import datetime
import time
from PIL import Image
import io
from pathlib import Path
import uuid
import logging
from .resize import resize_to_1024
logger = logging.getLogger(__name__)

# 定义两个目录（在项目根目录下）
UPLOAD_DIR = Path("uploads/sketch")
OUTPUT_DIR = Path("outputs")

# 确保目录存在
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)



def save_output_image(image: Image.Image, prefix: str = "generated") -> Path:
    """
    保存 ComfyScript 生成的图片到 outputs/ 目录
    返回相对路径（如 "outputs/20260413_085412_generated_123456.png"），供前端使用
    """
    if image is None:
        raise ValueError("生成的图片为空")

    try:
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_id = uuid.uuid4().hex[:8]  # 使用 uuid 更安全
        filename = f"{timestamp}_{prefix}_{random_id}.png"

        output_path = OUTPUT_DIR / filename

        image = resize_to_1024(image)
        image.save(output_path, format="PNG")

        logger.info(f"生成图片已保存: {output_path}")
        print(f"生成图片路径: {output_path}")  # 方便你调试

        return output_path  # ← 修改为返回 Path 对象

    except Exception as e:
        logger.error(f"保存生成图片失败: {e}")
        raise


def save_uploaded_image(sketch_file, prefix: str = "uploaded") -> Path:
    """
    保存用户上传的草图
    注意：这里接收的是已经 await 读取后的 bytes，或者在调用前处理
    """
    try:
        # 正确处理 FastAPI UploadFile
        if hasattr(sketch_file, 'read') and callable(sketch_file.read):
            # 关键：不能在这里 await，必须在上层 await 后再传进来
            # 所以我们改策略：让上层先 await read()
            raise ValueError("请在上层 await sketch_file.read() 后再调用此函数")

        # 如果已经传进来的是 bytes
        if isinstance(sketch_file, (bytes, bytearray)):
            contents = sketch_file
        else:
            contents = sketch_file  # 假设已经是 bytes

        image = Image.open(io.BytesIO(contents)).convert("RGB")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_id = uuid.uuid4().hex[:8]  # 使用 uuid 更安全
        filename = f"{timestamp}_{prefix}_{random_id}.png"
        upload_path = UPLOAD_DIR / filename

        image = resize_to_1024(image)
        image.save(upload_path, format="PNG")

        logger.info(f"上传草图已保存: {upload_path}")
        return upload_path

    except Exception as e:
        logger.error(f"保存上传草图失败: {e}")
        raise

def get_output_url(output_path: Path) -> str:
    """根据保存路径生成前端可访问的 URL"""
    return f"/outputs/{output_path.name}"

def get_upload_url(upload_path: Path) -> str:
    """根据上传路径生成前端可访问的 URL"""
    return f"/uploads/sketch/{upload_path.name}"