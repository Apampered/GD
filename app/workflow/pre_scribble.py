import cv2
import numpy as np
import matplotlib.pyplot as plt

# -------------------------------
# 读取草图（建议用灰度或黑白扫描图）
# -------------------------------
img_path = "../../{6DA5AC90-FE0F-4c2e-87FE-AA02EAB6E1BE}.png"  # ← 改成你的草图路径
# img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
#
# if img is None:
#     print("图片读取失败，请检查路径")
#     exit()
#
# # -------------------------------
# # Step 1: 二值化（推荐Otsu或自适应）
# # -------------------------------
# # 方法A：全局Otsu（适合对比度较好的草图）
# _, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
#
# # 方法B：自适应阈值（更适合光照不均的扫描草图）
# # binary = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
# #                                cv2.THRESH_BINARY, 11, 2)
#
# # 反转（让线条变成白色，前景为255）
# binary = cv2.bitwise_not(binary)
#
# # -------------------------------
# # Step 2: 形态学操作 - 连接断笔 & 去除小噪声
# # -------------------------------
# # 内核大小根据你的笔触间隙调整（3~15都很常见）
# kernel_size = 5
# kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
#
# # 先闭运算 → 连接断开的笔触、填小孔
# closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
#
# # 再开运算 → 去除小的孤立噪点和毛刺
# cleaned = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel, iterations=1)
#
#
# # 可选：轻微腐蚀，让线条更干净（如果还太粗）
# # cleaned = cv2.erode(cleaned, kernel, iterations=1)
#
# # -------------------------------
# # Step 3: 细化（Thinning / Skeletonization）→ 统一线宽为1像素
# # -------------------------------
# # OpenCV没有内置Zhang-Suen细化，但可以用这个简单近似方法
# # 或者直接用 skimage 的 skeletonize（更准确）
# # 这里先展示 OpenCV 常用方式：多次腐蚀 + 减法近似细化
#
# def simple_thinning(img_binary):
#     """非常简易的 thinning（效果有限，适合快速预览）"""
#     size = np.size(img_binary)
#     skel = np.zeros(img_binary.shape, np.uint8)
#
#     element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
#     done = False
#
#     while not done:
#         eroded = cv2.erode(img_binary, element)
#         temp = cv2.dilate(eroded, element)
#         temp = cv2.subtract(img_binary, temp)
#         skel = cv2.bitwise_or(skel, temp)
#         img_binary = eroded.copy()
#
#         if cv2.countNonZero(img_binary) == 0:
#             done = True
#
#     return skel
#
#
# # thinned = simple_thinning(cleaned)   # 取消注释使用
#
# # 更好的方式：安装 scikit-image 后使用（推荐）
# # from skimage.morphology import skeletonize
# # thinned = skeletonize(cleaned // 255) * 255
#
# # 这里暂时用 cleaned 作为最终结果（如果你不需要单像素线条）
#
# # -------------------------------
# # 显示对比
# # -------------------------------
# titles = ['原图', '二值化', '闭运算后', '清理后 (推荐)']
# images = [img, binary, closed, cleaned]
#
# plt.figure(figsize=(12, 8))
# for i in range(len(images)):
#     plt.subplot(2, 2, i + 1)
#     plt.imshow(images[i], 'gray')
#     plt.title(titles[i])
#     plt.axis('off')
#
# plt.tight_layout()
# plt.show()
#
# # 保存结果
# cv2.imwrite("cleaned_sketch.png", cleaned)
# # cv2.imwrite("thinned_sketch.png", thinned)  # 如果用了细化
def preprocess_sketch(input_path, output_path, canny_low=100, canny_high=200, blur_kernel=5, dilate_kernel=3):
    """
    草图预处理：去噪 + 边缘提取 + 线条增强
    :param input_path: 输入草图路径 (e.g., 'sketch.jpg')
    :param output_path: 输出路径 (e.g., 'preprocessed_sketch.png')
    :param canny_low/high: Canny阈值
    :param blur_kernel: 高斯模糊核大小 (奇数)
    :param dilate_kernel: 膨胀核大小
    """
    # 读取图像
    img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError("无法读取图像，请检查路径")

    # 高斯模糊去噪
    blurred = cv2.GaussianBlur(img, (blur_kernel, blur_kernel), 0)

    # Canny边缘检测
    edges = cv2.Canny(blurred, canny_low, canny_high)

    # 膨胀增强线条
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (dilate_kernel, dilate_kernel))
    dilated = cv2.dilate(edges, kernel)

    # 保存结果
    cv2.imwrite(output_path, dilated)
    print(f"预处理完成，输出到: {output_path}")
    return dilated  # 返回numpy array，便于后续使用

# 示例调用
if __name__ == "__main__":
    preprocess_sketch("../../{6DA5AC90-FE0F-4c2e-87FE-AA02EAB6E1BE}.png", "preprocessed_sketch.png")