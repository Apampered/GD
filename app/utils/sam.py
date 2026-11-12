from segment_anything import sam_model_registry, SamAutomaticMaskGenerator, SamPredictor
import cv2
import numpy as np
from huggingface_hub import hf_hub_download  # 下载模型权重


def sam_segment(input_path, output_foreground_path, output_background_path, model_type="vit_h", checkpoint_path=None):
    """
    用SAM分割图像，分开前景和背景
    :param input_path: 输入图像路径 (e.g., 'image.jpg'，可以是草图或生成的图)
    :param output_foreground_path: 前景输出路径
    :param output_background_path: 背景输出路径
    :param model_type: SAM模型类型 ('vit_h' 大模型，'vit_b' 小)
    :param checkpoint_path: 模型权重路径 (None时自动下载)
    """
    # 下载/加载模型
    if checkpoint_path is None:
        checkpoint_path = hf_hub_download(repo_id="facebook/sam-vit-huge", filename="sam_vit_h_4b8939.pth")  # 示例用vit_h
    sam = sam_model_registry[model_type](checkpoint=checkpoint_path)
    sam.to(device='cuda' if torch.cuda.is_available() else 'cpu')  # 用GPU加速

    # 自动mask生成器（无prompt，全自动分割）
    mask_generator = SamAutomaticMaskGenerator(sam)

    # 读图
    image = cv2.imread(input_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # 生成masks
    masks = mask_generator.generate(image_rgb)

    # 简单逻辑：取最大的mask作为前景（假设主体最大）
    if not masks:
        raise ValueError("未检测到分割！")
    largest_mask = max(masks, key=lambda x: x['area'])['segmentation']  # bool array

    # 分离前景/背景
    foreground = image.copy()
    foreground[~largest_mask] = 0  # 背景设黑

    background = image.copy()
    background[largest_mask] = 0  # 前景设黑

    # 保存
    cv2.imwrite(output_foreground_path, foreground)
    cv2.imwrite(output_background_path, background)
    print(f"分割完成，前景: {output_foreground_path}, 背景: {output_background_path}")
    return foreground, background


# 示例调用（需import torch）
if __name__ == "__main__":
    import torch

    sam_segment('input_image.jpg', 'foreground.png', 'background.png')