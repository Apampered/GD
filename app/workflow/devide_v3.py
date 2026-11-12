import ast
import asyncio
from comfy_script.runtime import *
# 连接到本地 ComfyUI）
load('http://127.0.0.1:8188/')
from typing import Annotated
from comfy_script.runtime.nodes import SetLatentNoiseMask, EmptyImage, GetImageSize, ImageScale, LoadImage, DownloadAndLoadFlorence2Model, Florence2Run, PreviewImage, DownloadAndLoadSAM2Model, Florence2toCoordinates, Sam2Segmentation, MaskPreview, MaskToImage, SomethingToString, ShowTextPysssss, CheckpointLoaderSimple, CLIPTextEncode, ConditioningCombine, ControlNetLoader, ImageInvert, ControlNetApplyAdvanced, EmptyLatentImage, KSampler, VAEDecode, VAEEncode, Canny, CannyEdgePreprocessor, ImageCompositeMasked, InvertMask, GrowMask, WD14TaggerPysssss

from app.utils.image_utils import save_output_image

from pathlib import Path

def generate_from_sketch(
        sketch_image: Path,
        style: str,
        strength: float,
        seed: int = None,
        # 其他参数...
):
    with Workflow():
        sketch_image = '{6DA5AC90-FE0F-4c2e-87FE-AA02EAB6E1BE} (1).png'
        image, _ = LoadImage(sketch_image)
        image = ImageScale(image=image, upscale_method='nearest-exact', width=1024, height=1024, crop='disabled')
        florence2_model = DownloadAndLoadFlorence2Model(model='microsoft/Florence-2-base', precision='fp16', attention='sdpa', convert_to_safetensors=False)
        image2, _, caption, data = Florence2Run(image=image, florence2_model=florence2_model, text_input='', task='region_caption', fill_mask=False, keep_model_loaded=False, max_new_tokens=512, num_beams=3, do_sample=False, output_mask_select='', seed=736122380147644)
        PreviewImage(image2)
        # _ = ShowTextPysssss(caption)
        sam2_model = DownloadAndLoadSAM2Model(model='sam2.1_hiera_base_plus.safetensors', segmentor='single_image', device='cuda', precision='fp16')
        center_coordinates, bboxes = Florence2toCoordinates(data=data, index='0', batch=False)
        mask = Sam2Segmentation(sam2_model=sam2_model, image=image, keep_model_loaded=False, coordinates_positive=center_coordinates, bboxes=bboxes, individual_objects=True)
        MaskPreview(mask)
        # data = SomethingToString(input=data, prefix='', suffix='')
        # # _ = ShowTextPysssss(data)
        width, height, count = GetImageSize(image)
        image3 = EmptyImage(width=width, height=height, batch_size=count, color=16777215)
        center_coordinates2, bboxes2 = Florence2toCoordinates(data=data, index='', batch=False)
        mask2 = Sam2Segmentation(sam2_model=sam2_model, image=image,
                                 keep_model_loaded=False, coordinates_positive=center_coordinates2,
                                 bboxes=bboxes2, individual_objects=True)

        mask2 = InvertMask(mask2)
        mask3 = GrowMask(mask=mask2, expand=-20, tapered_corners=True)

        model, clip, vae = CheckpointLoaderSimple('oneObsession_v18.safetensors')

        center_coordinates3, bboxes3 = Florence2toCoordinates(data=data, index='1', batch=False)
        mask4 = Sam2Segmentation(sam2_model=sam2_model, image=image,
                                 keep_model_loaded=False, coordinates_positive=center_coordinates3,
                                 bboxes=bboxes3, individual_objects=True)



        # 第一轮
        image4 = ImageCompositeMasked(destination=image3, source=image,
                                      x=0, y=0, resize_source=False, mask=mask3)
        PreviewImage(image4)
        image7 = ImageInvert(image4)
        # 应用controlnet
        conditioning5 = CLIPTextEncode('''vibrant colors, highly saturated, colorful palette, bright lighting, cinematic color grading, volumetric godrays, global illumination, sharp focus, high contrast, masterpiece, best quality,
        realistic natural colors, accurate real-world coloring, photorealistic tones, natural lighting, coherent environment, detailed textures matching real life, harmonious palette, high detail, best quality, masterpiece,
        green tree,beautiful scenery''', clip)
        florence2_model2 = DownloadAndLoadFlorence2Model(model='microsoft/Florence-2-base', precision='fp16', attention='sdpa', convert_to_safetensors=False)
        _, _, caption2, data2 = Florence2Run(image=image4, florence2_model=florence2_model2,
                                             text_input='', task='detailed_caption',
                                             fill_mask=False, keep_model_loaded=False,
                                             max_new_tokens=512, num_beams=3, do_sample=False,
                                             output_mask_select='', seed=221020294409291)
        conditioning6 = CLIPTextEncode(caption2, clip)
        conditioning7 = ConditioningCombine(conditioning5, conditioning6)
        conditioning8 = CLIPTextEncode('''monochrome, grayscale, black and white, desaturated, low saturation, dark shadows, overexposed, underexposed, foggy, dim lighting, muted colors, boring, low contrast,
        ''', clip)
        control_net1 = ControlNetLoader('xinsir_union.safetensors')
        positive1, negative1 = ControlNetApplyAdvanced(positive=conditioning7, negative=conditioning8,
                                                       control_net=control_net1, image=image7,
                                                       strength=1, start_percent=0, end_percent=1)
        latent1 = EmptyLatentImage(width=width, height=height, batch_size=count)
        latent1 = KSampler(model=model, seed=216041697659430,
                           steps=20, cfg=6, sampler_name='euler',
                           scheduler='normal', positive=positive1,
                           negative=negative1, latent_image=latent1, denoise=1)
        image11 = VAEDecode(latent1, vae)
        PreviewImage(image11)

        # 第二轮
        image5 = ImageCompositeMasked(destination=image3, source=image,
                                      x=0, y=0, resize_source=False, mask=mask4)
        PreviewImage(image5)
        image6 = ImageInvert(image5)
        PreviewImage(image6)
        conditioning1 = CLIPTextEncode('''vibrant colors, highly saturated, colorful palette, bright lighting, cinematic color grading, volumetric godrays, global illumination, sharp focus, high contrast, masterpiece, best quality,
        realistic natural colors, accurate real-world coloring, photorealistic tones, natural lighting, coherent environment, detailed textures matching real life, harmonious palette, high detail, best quality, masterpiece,
        a black car,''', clip)
        string = WD14TaggerPysssss(image=image5, model='wd-v1-4-moat-tagger-v2',
                                   threshold=0.35, character_threshold=0.85,
                                   replace_underscore=False, trailing_comma=False,
                                   exclude_tags='solo, simple_background, white_background, monochrome, greyscale')
        conditioning2 = CLIPTextEncode(string, clip)
        conditioning3 = ConditioningCombine(conditioning1, conditioning2)
        conditioning4 = CLIPTextEncode('''monochrome, grayscale, black and white, desaturated, low saturation, dark shadows, overexposed, underexposed, foggy, dim lighting, muted colors, boring, low contrast,
        ''', clip)
        control_net2 = ControlNetLoader('xinsir_union.safetensors')
        positive2, negative2 = ControlNetApplyAdvanced(positive=conditioning3, negative=conditioning4,
                                                       control_net=control_net2, image=image6,
                                                       strength=1, start_percent=0, end_percent=1)
        latent2 = SetLatentNoiseMask(latent1, mask4)
        latent2 = KSampler(model=model, seed=748976932817094,
                           steps=20, cfg=6, sampler_name='euler',
                           scheduler='normal', positive=positive2,
                           negative=negative2, latent_image=latent2, denoise=1)
        image8 = VAEDecode(latent2, vae)
        PreviewImage(image8)
        # 第三轮
        image13 = ImageCompositeMasked(destination=image3, source=image,
                                       x=0, y=0, resize_source=False, mask=mask)
        PreviewImage(image13)
        # _ = VAEEncode(image13, vae)
        image14 = ImageInvert(image13)
        PreviewImage(image14)
        conditioning9 = CLIPTextEncode('''vibrant colors, highly saturated, colorful palette, bright lighting, cinematic color grading, volumetric godrays, global illumination, sharp focus, high contrast, masterpiece, best quality,
        realistic natural colors, accurate real-world coloring, photorealistic tones, natural lighting, coherent environment, detailed textures matching real life, harmonious palette, high detail, best quality, masterpiece,
        a black car,
        a wood house,''', clip)
        string2 = WD14TaggerPysssss(image=image13, model='wd-v1-4-moat-tagger-v2',
                                    threshold=0.35, character_threshold=0.85,
                                    replace_underscore=False, trailing_comma=False,
                                    exclude_tags='solo, simple_background,comic, white_background, monochrome, greyscale')
        conditioning10 = CLIPTextEncode(string2, clip)
        conditioning11 = ConditioningCombine(conditioning9, conditioning10)
        conditioning12 = CLIPTextEncode('''monochrome, grayscale, black and white, desaturated, low saturation, dark shadows, overexposed, underexposed, foggy, dim lighting, muted colors, boring, low contrast,
        ''', clip)
        control_net3 = ControlNetLoader('xinsir_union.safetensors')

        # 应用controlnet
        positive3, negative3 = ControlNetApplyAdvanced(positive=conditioning11, negative=conditioning12,
                                                       control_net=control_net3, image=image14,
                                                       strength=1, start_percent=0,
                                                       end_percent=1, vae=vae)
        latent3 = SetLatentNoiseMask(latent2, mask)
        latent3 = KSampler(model=model, seed=748976932817094,
                           steps=20, cfg=6, sampler_name='euler',
                           scheduler='normal', positive=positive3,
                           negative=negative3, latent_image=latent3,
                           denoise=1)
        image15 = VAEDecode(latent3, vae)
        image_show = util.get_images(image15)
        image_show[0].show()
        output_path = save_output_image(image_show[0])

        print('finish')
        return output_path

