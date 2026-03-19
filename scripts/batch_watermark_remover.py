#!/usr/bin/env python3
"""
批量去除图片水印工具
参考模板匹配方法实现
"""

import cv2
import numpy as np
import os
import sys
from PIL import Image

def select_template(img):
    """
    手动选择水印区域作为模板
    返回模板图像和位置
    """
    # 显示图像，让用户选择区域
    # 这里使用简单的坐标输入方式
    return None

def template_match_remove(img, template, threshold=0.8):
    """
    使用模板匹配找到水印位置并去除
    """
    if template is None:
        return img, 0
    
    # 转换为灰度
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    
    if len(template.shape) == 3:
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    else:
        template_gray = template
    
    # 模板匹配
    result = cv2.matchTemplate(gray, template_gray, cv2.TM_CCOEFF_NORMED)
    
    # 找到匹配位置
    locations = np.where(result >= threshold)
    
    # 创建mask
    h, w = template_gray.shape
    mask = np.zeros(gray.shape, dtype=np.uint8)
    
    count = 0
    for pt in zip(*locations[::-1]):
        x, y = pt
        mask[y:y+h, x:x+w] = 255
        count += 1
    
    print(f"找到 {count} 个匹配位置")
    
    if count > 0:
        # 扩大mask
        kernel = np.ones((3,3), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=2)
        
        # inpaint
        result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
        return result, count
    
    return img, 0

def manual_region_remove(img, x1, y1, x2, y2):
    """
    手动指定区域并自动扩展去除
    """
    h, w = img.shape[:2]
    
    # 确保坐标有效
    x1, x2 = max(0, min(x1, x2)), min(w, max(x1, x2))
    y1, y2 = max(0, min(y1, y2)), min(h, max(y1, y2))
    
    # 创建模板
    template = img[y1:y2, x1:x2]
    
    print(f"模板区域: ({x1}, {y1}) - ({x2}, {y2})")
    
    # 使用模板匹配找到所有类似区域
    return template_match_remove(img, template, threshold=0.7)

def inpaint_region(img, x1, y1, x2, y2):
    """
    简单区域去除
    """
    h, w = img.shape[:2]
    
    # 确保坐标有效
    x1, x2 = max(0, min(x1, x2)), min(w, max(x1, x2))
    y1, y2 = max(0, min(y1, y2)), min(h, max(y1, y2))
    
    # 创建mask
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    padding = 5
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(w, x2 + padding)
    y2 = min(h, y2 + padding)
    mask[y1:y2, x1:x2] = 255
    
    # inpaint
    result = cv2.inpaint(img, mask, 5, cv2.INPAINT_TELEA)
    
    # 增强
    result = enhance(result)
    
    return result

def enhance(img):
    """增强图像"""
    if len(img.shape) == 3:
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        result = cv2.merge([l, a, b])
        return cv2.cvtColor(result, cv2.COLOR_LAB2BGR)
    else:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        return clahe.apply(img)

def batch_process(input_dir, output_dir, region=None):
    """
    批量处理目录下的图片
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 获取所有图片
    extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    files = [f for f in os.listdir(input_dir) 
             if any(f.lower().endswith(ext) for ext in extensions)]
    
    print(f"找到 {len(files)} 张图片")
    
    for i, filename in enumerate(files):
        print(f"处理 {i+1}/{len(files)}: {filename}")
        
        img_path = os.path.join(input_dir, filename)
        img = cv2.imread(img_path)
        
        if img is None:
            print(f"  无法读取: {filename}")
            continue
        
        if region:
            result = inpaint_region(img, *region)
        else:
            # 默认处理右上角
            h, w = img.shape[:2]
            result = inpaint_region(img, int(w*0.7), int(h*0.1), int(w*0.95), int(h*0.4))
        
        output_path = os.path.join(output_dir, filename)
        cv2.imwrite(output_path, result)
        print(f"  ✅ 已保存: {output_path}")

def main():
    print("=" * 50)
    print("🧹 批量水印去除工具")
    print("=" * 50)
    print("""
用法:
  python batch_watermark_remover.py <图片> <输出> [x1 y1 x2 y2]
  python batch_watermark_remover.py <输入目录> <输出目录>
  python batch_watermark_remover.py <图片> <输出> auto
""")
    
    if len(sys.argv) < 3:
        print("请提供参数")
        return
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    if os.path.isdir(input_path):
        # 批量处理目录
        batch_process(input_path, output_path)
    elif os.path.isfile(input_path):
        # 单文件处理
        img = cv2.imread(input_path)
        if img is None:
            print(f"无法读取: {input_path}")
            return
        
        if len(sys.argv) > 4:
            # 指定区域
            try:
                x1 = int(sys.argv[3])
                y1 = int(sys.argv[4])
                x2 = int(sys.argv[5])
                y2 = int(sys.argv[6])
                result = inpaint_region(img, x1, y1, x2, y2)
            except:
                print("区域参数错误")
                result = img
        elif len(sys.argv) == 4 and sys.argv[3] == 'auto':
            # 自动检测
            h, w = img.shape[:2]
            # 默认处理可能的水印区域
            result = inpaint_region(img, int(w*0.7), int(h*0.1), int(w*0.95), int(h*0.35))
        else:
            # 默认
            h, w = img.shape[:2]
            result = inpaint_region(img, int(w*0.7), int(h*0.1), int(w*0.95), int(h*0.35))
        
        cv2.imwrite(output_path, result)
        print(f"✅ 已保存: {output_path}")

if __name__ == "__main__":
    main()
