import ast
import asyncio
from comfy_script.runtime import *
# 连接到本地 ComfyUI）
load('http://127.0.0.1:8188/')
from typing import Annotated
from comfy_script.runtime.nodes import LoadImage, PreviewImage, CheckpointLoaderSimple, CLIPTextEncode, VAEEncode, SetLatentNoiseMask, KSampler, VAEDecode, SaveImage, ImageToMask, ImpactGaussianBlurMask, GetImageSize, ImageScale, LoadImageFromUrlMtb

from app.utils.image_utils import save_output_image

def inpainting_workflow(
        original_image: str = 'http://127.0.0.1:8000/outputs/20260414_183021_generated_815512.png',
        mask_image: str = 'http://127.0.0.1:8000/outputs/20260414_183021_generated_815512.png',
        prompt: str = '',
        strength: float = 1,
        seed: int = None,
        # 其他参数...
):
    print(original_image, mask_image)
    with Workflow():
        model, clip, vae = CheckpointLoaderSimple('oneObsession_v18.safetensors')
        conditioning = CLIPTextEncode(f'{prompt}',clip)
        conditioning2 = CLIPTextEncode(
            '''text, watermark, signature, logo, brand, username, copyright, title, letter, word, writing, text overlay, subtitle,
monochrome, black and white, greyscale, lineart, sketch, drawing, outline, ink sketch, pencil sketch,
nsfw, nude, naked, topless, bottomless, explicit, erotic, porn, pornography, sex, sexual, intercourse, 
breasts, nipples, vagina, penis, pussy, asshole, cum, semen, ejaculation, censored, bar censor, mosaic censor,
low quality, worst quality, blurry, deformed, ugly, distorted, bad anatomy, extra limbs, missing limbs, 
poorly drawn hands, poorly drawn face, mutation, mutated, extra fingers, fused fingers, too many fingers, 
bad proportions, lowres, jpeg artifacts, compression artifacts, duplicate, morbid, mutilated''',
            clip)
        image = LoadImageFromUrlMtb(original_image)
        latent = VAEEncode(image, vae)
        mask_image = LoadImageFromUrlMtb(mask_image)
        mask = ImageToMask(mask_image, 'red')
        mask = ImpactGaussianBlurMask(mask=mask, kernel_size=5, sigma=10)
        latent = SetLatentNoiseMask(latent, mask)
        latent = KSampler(model=model, seed=606639118782371, steps=30, cfg=8, sampler_name='dpmpp_2m',
                          scheduler='karras', positive=conditioning, negative=conditioning2, latent_image=latent,
                          denoise=strength)
        image3 = VAEDecode(latent, vae)
        image_show = util.get_images(image3)
        # image_show[0].show()

        output_path = save_output_image(image_show[0])
        return output_path

if __name__ == "__main__":
    inpainting_workflow()
