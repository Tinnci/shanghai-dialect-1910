import cv2
import os
import glob
import numpy as np

def process_image(input_path, output_path):
    print(f"Processing: {input_path}")
    
    # 1. 读取图像 (Read Image)
    img = cv2.imread(input_path)
    if img is None:
        print(f"Failed to load image: {input_path}")
        return

    # 2. 灰度化 (Grayscale)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. 去噪 (Denoising) - 使用较弱的高斯模糊以保留更多细节
    # kernel size (3, 3) 比 (5, 5) 模糊更少，保留笔画边缘
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # 4. 对比度增强 (Contrast Enhancement)
    # 降低 clipLimit (2.0 -> 1.0) 以避免过度放大由于纸背渗透造成的背景噪声
    clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(blurred)

    # 5. 二值化 (Binarization) - 自适应阈值
    # 增大 blockSize (15 -> 21) 以更好地感测局部背景
    # 提高 C 值 (8 -> 15) 增加过滤强度，只有显著黑于背景的像素才会被认为是文字
    # 这能有效抑制透背噪声 (bleed-through)
    binary = cv2.adaptiveThreshold(
        enhanced, 
        255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 
        21, 
        15 
    )

    # 6. 去除小噪点 (Despeckle) - 使用连通域分析
    # 减小 min_size (15 -> 8) 以避免误删微小的标点或笔画末端
    binary = remove_small_noise(binary, min_size=8)
    
    # 保存结果
    cv2.imwrite(output_path, binary)
    print(f"Saved to: {output_path}")

def remove_small_noise(img, min_size=15):
    """
    移除二值图像中面积小于 min_size 的黑色噪点（假设背景为白色）。
    """
    # 1. 反转图像，使文字/噪点变成白色（前景），背景变成黑色
    img_inv = cv2.bitwise_not(img)
    
    # 2. 连通域分析
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(img_inv, connectivity=8)
    
    # 3. 找出所有面积小于阈值的连通域标签
    # stats[:, 4] 是面积 (CC_STAT_AREA)
    # 跳过 label 0 (背景)
    sizes = stats[:, cv2.CC_STAT_AREA]
    small_components = [i for i in range(1, num_labels) if sizes[i] < min_size]
    
    # 4. 如果没有噪点，直接返回
    if not small_components:
        return img

    # 5. 将这些小连通域 mask 掉
    # 使用 numpy 快速操作
    # 创建一个 mask，如果 labels 在 small_components 中，则为 True
    # 为了效率，我们直接修改 img_inv
    # 这种逐像素赋值在 Python 中可能慢，改为利用 labels 图像重绘大组件更高效
    # 但 numpy 下 mask 赋值也很快:
    mask = np.isin(labels, small_components)
    img_inv[mask] = 0 # 擦除噪点（变黑）
    
    # 6. 反转回白底黑字
    return cv2.bitwise_not(img_inv)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, "92_embedded-images")
    output_dir = os.path.join(base_dir, "93_processed-images")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 支持常见的图像格式
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tif']
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(input_dir, ext)))
        # 大小写兼容
        files.extend(glob.glob(os.path.join(input_dir, ext.upper())))

    files = sorted(list(set(files))) # 去重并排序

    print(f"Found {len(files)} images to process.")

    for file_path in files:
        filename = os.path.basename(file_path)
        output_path = os.path.join(output_dir, filename)
        process_image(file_path, output_path)

    print("All processing complete.")

if __name__ == "__main__":
    main()
