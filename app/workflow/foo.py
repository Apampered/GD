import faulthandler
faulthandler.enable()
# 放代码最开头
import random
import torch
import numpy as np
import cv2
from PIL import Image
from diffusers import ControlNetModel, StableDiffusionXLControlNetPipeline, AutoencoderKL
from diffusers import EulerAncestralDiscreteScheduler
from diffusers.utils import load_image
from controlnet_aux import HEDdetector  # 用于提取边缘（模拟 scribble）
import torch
print("CUDA available:", torch.cuda.is_available())
print("Device count:", torch.cuda.device_count())
print("Current device:", torch.cuda.current_device())
print("Device name:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")
# ====================== 你的本地模型路径 ======================
xl_model = r"D:\Confy\models\checkpoints\oneObsession_v18.safetensors"
controlnet_model = r"D:\study\xinsir_scribble.safetensors"

# ====================== 参数设置 ======================
controlnet_conditioning_scale = 0.8  # Union 模型建议 0.6~1.0，根据效果调
prompt = "masterpiece, best quality, a beautiful girl in fantasy dress, detailed background, cinematic lighting"
negative_prompt = "worst quality, low quality, bad anatomy, deformed, blurry, extra limbs, missing fingers"

# ====================== 调度器（从 SDXL base 兼容的 scheduler） ======================
# 因为你的 checkpoint 是 SDXL 系的，用 Euler a 通常效果好
scheduler = EulerAncestralDiscreteScheduler.from_config({
    "prediction_type": "epsilon",
    "timestep_spacing": "leading",
    "rescale_betas_zero_snr": True,  # SDXL 常见优化
})

# ====================== 加载 ControlNet (Union ProMax 单文件) ======================
controlnet = ControlNetModel.from_single_file(
    controlnet_model,
    torch_dtype=torch.float32,  # 避免 fp16 精度/内存问题
    use_safetensors=True,
    low_cpu_mem_usage=True,
)
print('controlnet加载')
# ====================== 加载主模型 (你的 oneObsession_v18 单文件) ======================
pipe = StableDiffusionXLControlNetPipeline.from_single_file(
    xl_model,
    controlnet=controlnet,
    torch_dtype=torch.float32,
    safety_checker=None,
    scheduler=scheduler,
    variant="fp16",  # 保留，但 dtype 先 float32
    low_cpu_mem_usage=True,
)

# 可选：用更好的 VAE（如果你的 checkpoint 自带 VAE 不理想，可换这个）
# pipe.vae = AutoencoderKL.from_pretrained("madebyollin/sdxl-vae-fp16-fix", torch_dtype=torch.float16)
print("模型加载完成（CPU 模式）！现在测试移动到 GPU...")
# 移动到 GPU 并优化显存
pipe.enable_vae_slicing()          # VAE 分片处理 latent，省很多
pipe.enable_vae_tiling()           # 如果分辨率大，加这个
pipe.enable_model_cpu_offload()
# ====================== 预处理器函数 ======================
def nms(x, t, s):
    x = cv2.GaussianBlur(x.astype(np.float32), (0, 0), s)
    f1 = np.array([[0, 0, 0], [1, 1, 1], [0, 0, 0]], dtype=np.uint8)
    f2 = np.array([[0, 1, 0], [0, 1, 0], [0, 1, 0]], dtype=np.uint8)
    f3 = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=np.uint8)
    f4 = np.array([[0, 0, 1], [0, 1, 0], [1, 0, 0]], dtype=np.uint8)
    y = np.zeros_like(x)
    for f in [f1, f2, f3, f4]:
        np.putmask(y, cv2.dilate(x, kernel=f) == x, x)
    z = np.zeros_like(y, dtype=np.uint8)
    z[y > t] = 255
    return z

# ====================== 生成 control image ======================
# 这里用 HED 提取边缘（类似原代码的 scribble 效果）
# 你也可以换成 cv2.Canny() 或其他 preprocessor
input_image_path = r"/{6DA5AC90-FE0F-4c2e-87FE-AA02EAB6E1BE}.png"  # ← 替换成你的参考图路径

input_image = cv2.imread(input_image_path)
processor = HEDdetector.from_pretrained('lllyasviel/Annotators')
hed_image = processor(input_image, scribble=False)  # scribble=True 会更粗

control_image = np.array(hed_image)
control_image = nms(control_image, 127, 3)
control_image = cv2.GaussianBlur(control_image, (0, 0), 3)

# 随机细线条阈值（模拟手绘感）
random_val = int(round(random.uniform(0.01, 0.12), 2) * 255)
control_image[control_image > random_val] = 255
control_image[control_image < 255] = 0

control_image = Image.fromarray(control_image).convert("RGB")

# 调整到 SDXL 推荐分辨率（1024 附近）
width, height = control_image.size
ratio = np.sqrt(512. * 512. / (width * height))
new_width, new_height = int(width * ratio // 8 * 8), int(height * ratio // 8 * 8)  # 必须 8 的倍数
control_image = control_image.resize((new_width, new_height), Image.LANCZOS)

# ====================== 推理 ======================
images = pipe(
    prompt=prompt,
    negative_prompt=negative_prompt,
    image=control_image,                     # control image
    controlnet_conditioning_scale=controlnet_conditioning_scale,
    control_type=torch.tensor([2]),
    width=new_width,
    height=new_height,
    num_inference_steps=30,
    guidance_scale=7.0,
).images

images[0].save("output.png")
print("生成完成：output.png")