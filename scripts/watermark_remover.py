#!/usr/bin/env python3
"""
基于模板匹配的水印去除工具
参考GitHub开源项目思路实现
"""

import cv2
import numpy as np
import os
import sys

def select_roi(img):
    """
    交互式选择ROI区域（需要图形界面）
    """
    from matplotlib import pyplot as plt
    
    # 显示图像
    plt.figure(figsize=(10, 8))
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.title('点击并拖动选择水印区域，按Enter确认')
    plt.subplots_adjust(bottom=0.2)
    
    # 简单实现：返回整个图像
    # 实际使用需要图形界面
    h, w = img.shape[:2]
    return img[0:h//3, 0:w//3]  # 默认取左上角1/3

def template_match_inpaint(img_path, template_roi, output_path=None, threshold=0.7):
    """
    使用模板匹配找到水印位置并去除
    
    参数:
        img_path: 图片路径
        template_roi: 模板图像（从原图中截取的水印区域）
        output_path: 输出路径
        threshold: 匹配阈值 (0-1)，越低匹配越多
    """
    # 读取图像
    img = cv2.imread(img_path)
    if img is None:
        print(f"无法读取图片: {img_path}")
        return False
    
    # 转为灰度
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    
    # 模板也转灰度
    if len(template_roi.shape) == 3:
        template = cv2.cvtColor(template_roi, cv2.COLOR_BGR2GRAY)
    else:
        template = template_roi.copy()
    
    h, w = gray.shape
    th, tw = template.shape
    
    print(f"图片尺寸: {w}x{h}")
    print(f"模板尺寸: {tw}x{th}")
    
    # 模板匹配 - 使用多种方法
    methods = ['TM_CCOEFF_NORMED', 'TM_CCORR_NORMED', 'TM_SQDIFF_NORMED']
    
    best_mask = None
    max_matches = 0
    
    for method_name in methods:
        method = getattr(cv2, method_name)
        
        # 匹配
        result = cv2.matchTemplate(gray, template, method)
        
        # 根据方法确定阈值
        if method_name == 'TM_SQDIFF_NORMED':
            # 越接近0越好
            locations = np.where(result <= (1 - threshold))
        else:
            # 越接近1越好
            locations = np.where(result >= threshold)
        
        # 创建mask
        mask = np.zeros(gray.shape, dtype=np.uint8)
        
        count = 0
        for pt in zip(*locations[::-1]):
            x, y = pt
            # 扩大一点区域
            x1 = max(0, x - 2)
            y1 = max(0, y - 2)
            x2 = min(w, x + tw + 2)
            y2 = min(h, y + th + 2)
            mask[y1:y2, x1:x2] = 255
            count += 1
        
        print(f"{method_name}: 找到 {count} 个匹配")
        
        if count > max_matches:
            max_matches = count
            best_mask = mask
    
    if best_mask is None or max_matches == 0:
        print("未找到匹配区域")
        # 直接inpaint整个角落
        best_mask = np.zeros(gray.shape, dtype=np.uint8)
        best_mask[0:h//3, 0:w//3] = 255  # 默认左上角
    
    # 形态学处理
    kernel = np.ones((3,3), np.uint8)
    best_mask = cv2.morphologyEx(best_mask, cv2.MORPH_CLOSE, kernel)
    best_mask = cv2.morphologyEx(best_mask, cv2.MORPH_OPEN, kernel)
    
    # 扩大修复区域
    best_mask = cv2.dilate(best_mask, kernel, iterations=2)
    
    print(f"Mask像素: {cv2.countNonZero(best_mask)}")
    
    # Inpaint
    result = cv2.inpaint(img, best_mask, 3, cv2.INPAINT_TELEA)
    
    # 可选：用NS方法
    result_ns = cv2.inpaint(img, best_mask, 3, cv2.INPAINT_NS)
    
    # 选择边缘更平滑的结果
    gray_result = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    gray_ns = cv2.cvtColor(result_ns, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edges_result = cv2.Canny(gray_result, 50, 150)
    edges_ns = cv2.Canny(gray_ns, 50, 150)
    
    score_result = np.sum(np.abs(edges - edges_result))
    score_ns = np.sum(np.abs(edges - edges_ns))
    
    print(f"TELEA得分: {score_result}, NS得分: {score_ns}")
    
    if score_ns < score_result:
        result = result_ns
        print("使用NS方法")
    
    # 增强
    result = enhance(result)
    
    if output_path is None:
        output_path = img_path.replace('.', '_inpainted.')
    
    cv2.imwrite(output_path, result)
    print(f"✅ 已保存: {output_path}")
    return True

def enhance(img):
    """增强图像"""
    if len(img.shape) == 3:
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        result = cv2.merge([l, a, b])
        return cv2.cvtColor(result, cv2.COLOR_LAB2BGR)
    return img

# 默认水印消除坐标（根据测试确定）
# 测试图片: test_img.jpg (1200x1200)
# 坐标: x(65-450), y(72-375)
DEFAULT_WATERMARK_REGION = {
    'x1': 65, 'y1': 72,
    'x2': 450, 'y2': 375
}

def process_with_coords(img_path, x1, y1, x2, y2, output_path=None):
    """
    使用坐标指定区域进行处理
    1. 提取指定区域作为模板
    2. 模板匹配找到所有类似区域
    3. Inpaint去除
    """
    img = cv2.imread(img_path)
    h, w = img.shape[:2]
    
    # 确保坐标有效
    x1, x2 = max(0, min(x1, x2)), min(w, max(x1, x2))
    y1, y2 = max(0, min(y1, y2)), min(h, max(y1, y2))
    
    print(f"选择区域: ({x1}, {y1}) - ({x2}, {y2})")
    
    # 提取模板
    template = img[y1:y2, x1:x2]
    
    return template_match_inpaint(img_path, template, output_path, threshold=0.6)

def batch_process(input_dir, output_dir, template_coords=None):
    """
    批量处理目录中的图片
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    files = [f for f in os.listdir(input_dir) 
             if any(f.lower().endswith(ext) for ext in extensions)]
    
    print(f"找到 {len(files)} 张图片")
    
    for i, filename in enumerate(files):
        print(f"\n处理 {i+1}/{len(files)}: {filename}")
        
        input_path = os.path.join(input_dir, filename)
        
        if template_coords:
            # 使用指定坐标
            x1, y1, x2, y2 = template_coords
            process_with_coords(input_path, x1, y1, x2, y2, 
                              os.path.join(output_dir, filename))
        else:
            # 默认处理
            img = cv2.imread(input_path)
            if img is None:
                continue
            h, w = img.shape[:2]
            # 默认处理右上角
            process_with_coords(input_path, int(w*0.7), int(h*0.1), 
                              int(w*0.95), int(h*0.35),
                              os.path.join(output_dir, filename))

def main():
    print("=" * 60)
    print("🔍 基于模板匹配的水印去除工具")
    print("=" * 60)
    print("""
用法:
  # 单图处理 - 自动模板匹配
  python watermark_remover.py <图片> <输出>
  
  # 单图处理 - 指定模板区域坐标
  python watermark_remover.py <图片> <输出> x1 y1 x2 y2
  
  # 批量处理
  python watermark_remover.py <输入目录> <输出目录> x1 y1 x2 y2
""")
    
    if len(sys.argv) < 3:
        print("参数不足")
        return
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    if os.path.isdir(input_path):
        # 批量处理
        if len(sys.argv) > 4:
            coords = (int(sys.argv[3]), int(sys.argv[4]), 
                     int(sys.argv[5]), int(sys.argv[6]))
            batch_process(input_path, output_path, coords)
        else:
            batch_process(input_path, output_path)
    else:
        # 单图处理
        if len(sys.argv) > 4:
            x1, y1, x2, y2 = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
            process_with_coords(input_path, x1, y1, x2, y2, output_path)
        else:
            # 自动处理 - 默认右上角
            img = cv2.imread(input_path)
            if img is not None:
                h, w = img.shape[:2]
                process_with_coords(input_path, int(w*0.7), int(h*0.1), 
                                 int(w*0.95), int(h*0.35), output_path)

if __name__ == "__main__":
    main()
