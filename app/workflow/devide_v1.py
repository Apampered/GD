import ast

from comfy_script.runtime import *
# 连接到本地 ComfyUI）
load('http://127.0.0.1:8188/')

from comfy_script.runtime.nodes import SetLatentNoiseMask, EmptyImage, GetImageSize, ImageScale, LoadImage, DownloadAndLoadFlorence2Model, Florence2Run, PreviewImage, DownloadAndLoadSAM2Model, Florence2toCoordinates, Sam2Segmentation, MaskPreview, MaskToImage, SomethingToString, ShowTextPysssss, CheckpointLoaderSimple, CLIPTextEncode, ConditioningCombine, ControlNetLoader, ImageInvert, ControlNetApplyAdvanced, EmptyLatentImage, KSampler, VAEDecode, VAEEncode, Canny, CannyEdgePreprocessor, ImageCompositeMasked, InvertMask, GrowMask, WD14TaggerPysssss

from app.utils.image_utils import save_output_image


def is_contained(small, large, iou_threshold=0.9):
    """判断 small 是否几乎完全被 large 包含"""
    sx1, sy1, sx2, sy2 = small
    lx1, ly1, lx2, ly2 = large

    # 完全包含判断（允许一点点边界溢出）
    if sx1 >= lx1 and sy1 >= ly1 and sx2 <= lx2 and sy2 <= ly2:
        return True

    # 或用 IoU > threshold 作为近似包含
    inter_x1 = max(sx1, lx1)
    inter_y1 = max(sy1, ly1)
    inter_x2 = min(sx2, lx2)
    inter_y2 = min(sy2, ly2)

    inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
    small_area = (sx2 - sx1) * (sy2 - sy1)

    if small_area == 0:
        return False

    iou = inter_area / small_area
    return iou >= iou_threshold

data_batch = []
with Workflow():
    image, _ = LoadImage('{6DA5AC90-FE0F-4c2e-87FE-AA02EAB6E1BE}.png')
    florence2_model = DownloadAndLoadFlorence2Model(model='microsoft/Florence-2-base', precision='fp16',
                                                    attention='sdpa', convert_to_safetensors=False)
    image2, _, caption, data = Florence2Run(image=image, florence2_model=florence2_model, text_input='',
                                            task='region_caption', fill_mask=False, keep_model_loaded=False,
                                            max_new_tokens=512, num_beams=3, do_sample=False, output_mask_select='',
                                            seed=786873987869931)
    print(str(data))
    data_mid = SomethingToString(input=data, prefix='', suffix='')
    show = ShowTextPysssss(data_mid)  # caption 作为输入
    result = show.wait()  # 等待执行完成
    text_list =ast.literal_eval(result._output['text'][0])
    filtered_text_list = []
    for i, box in enumerate(text_list):
        is_small_part = False
        for j, other in enumerate(text_list):
            if i == j:
                continue
            if is_contained(box, other):
                is_small_part = True
                break
        if not is_small_part:
            filtered_text_list.append(i)

    # print(f"原始 {len(text_list)} 个 → 过滤后 {len(filtered_text_list)} 个")
    # print("保留的框：", filtered_text_list)
    # print('num of mask:', len(text_list))
    # 获取了分割个数
    # TODO: 从 data 里获取分割个数,没考虑大包小包含情况的处理
    sam2_model = DownloadAndLoadSAM2Model(model='sam2.1_hiera_base_plus.safetensors', segmentor='single_image', device='cuda', precision='fp16')

    width, height, count = GetImageSize(image)
    empty_image = EmptyImage(width=width, height=height, batch_size=count, color=16777215)

    model, clip, vae = CheckpointLoaderSimple('oneObsession_v18.safetensors')

    latent = EmptyLatentImage(width=width, height=height, batch_size=count)

    print(filtered_text_list)
    for i in filtered_text_list:
        print(i)
        center_coordinates, bboxes = Florence2toCoordinates(data=data, index=f'{i}', batch=True)
        # util.get_str(center_coordinates)
        # util.get_str(bboxes)
        # for i, box in enumerate(bboxes.bboxes):
        #     x1, y1, x2, y2 = box
        #     print(f"框 {i}: left-top=({x1},{y1}), right-bottom=({x2},{y2})")
        #     width = x2 - x1
        #     height = y2 - y1

        # 获取mask
        mask = Sam2Segmentation(sam2_model=sam2_model, image=image, keep_model_loaded=False,
                                coordinates_positive=center_coordinates, bboxes=bboxes, individual_objects=True)

        image4 = ImageCompositeMasked(destination=empty_image, source=image,
                                      x=0, y=0, resize_source=False, mask=mask)
        PreviewImage(image4)
        image7 = ImageInvert(image4)
        # 应用controlnet
        conditioning5 = CLIPTextEncode('''vibrant colors, highly saturated, colorful palette, bright lighting, cinematic color grading, volumetric godrays, global illumination, sharp focus, high contrast, masterpiece, best quality,
                realistic natural colors, accurate real-world coloring, photorealistic tones, natural lighting, coherent environment, detailed textures matching real life, harmonious palette, high detail, best quality, masterpiece,
                green tree,beautiful scenery''', clip)
        florence2_model2 = DownloadAndLoadFlorence2Model(model='microsoft/Florence-2-base', precision='fp16',
                                                         attention='sdpa', convert_to_safetensors=False)
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
        latent = SetLatentNoiseMask(latent, mask)
        latent = KSampler(model=model, seed=216041697659430,
                           steps=20, cfg=6, sampler_name='euler',
                           scheduler='normal', positive=positive1,
                           negative=negative1, latent_image=latent, denoise=1)
    image11 = VAEDecode(latent, vae)
    PreviewImage(image11)
    # image_show = util.get_images(image11)
    # image_show[0].show()
    # output_path = save_generated_image(image_show[0])

    print('finish')