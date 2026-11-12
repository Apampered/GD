# app/services/image_resize.py
from PIL import Image
from pathlib import Path
from typing import Union, Optional
import logging

logger = logging.getLogger(__name__)

# 支持的插值方法映射
RESAMPLE_METHODS = {
    "nearest": Image.NEAREST,
    "bilinear": Image.BILINEAR,
    "bicubic": Image.BICUBIC,
    "lanczos": Image.LANCZOS,
    "hamming": Image.HAMMING,
    "box": Image.BOX,
}


def resize_image_to_long_side(
        image: Union[Image.Image, str, Path],
        target_long_side: int = 1024,
        resample: str = "bicubic",
        keep_aspect_ratio: bool = True,
) -> Image.Image:
    if isinstance(image, (str, Path)):
        img = Image.open(image).convert("RGB")
    else:
        img = image.convert("RGB")

    # 计算缩放比例
    width, height = img.size
    if width > height:
        new_width = target_long_side
        new_height = int(height * target_long_side / width)
    else:
        new_height = target_long_side
        new_width = int(width * target_long_side / height)

    resample_method = RESAMPLE_METHODS.get(resample.lower(), Image.BICUBIC)

    resized_img = img.resize((new_width, new_height), resample=resample_method)

    logger.info(f"图片缩放完成: {width}x{height} → {new_width}x{new_height} (方法: {resample})")

    return resized_img

def resize_to_1024(image: Union[Image.Image, str, Path], resample: str = "bicubic") -> Image.Image:
    """快速缩放到长边1024"""
    return resize_image_to_long_side(image, target_long_side=1024, resample=resample)


# 示例用法
if __name__ == "__main__":
    # 测试
    test_img = Image.new('RGB', (1920, 1080), color='blue')
    resized = resize_to_1024(test_img, resample="lanczos")
    print(f"缩放后尺寸: {resized.size}")