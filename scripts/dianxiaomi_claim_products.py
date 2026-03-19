#!/usr/bin/env python3
"""
店小秘产品认领自动化脚本
功能：从黄小惠店铺搬家产品到PETDUNIN店铺

流程：
1. 数据搬家 → 速卖通数据 → 黄小惠 → 未认领 → 全选 → 批量认领 → PETDUNIN
"""

from playwright.sync_api import sync_playwright
import time

def login_and_claim_products():
    with sync_playwright() as p:
        # 启动浏览器（非无头模式，方便看到操作）
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        # 1. 打开店小秘登录页
        print("📍 步骤1: 打开店小秘登录页...")
        page.goto('https://www.dianxiaomi.com/')
        page.wait_for_load_state('networkidle')
        
        # 2. 填写账号密码
        print("📍 步骤2: 填写账号密码...")
        page.fill('input[placeholder*="用户名"]', 'US_Adam')
        page.fill('input[placeholder*="密码"]', 'Adc10086')
        
        # 3. 点击登录
        print("📍 步骤3: 点击登录...")
        page.click('button:has-text("登录")')
        
        # 等待可能的验证码
        time.sleep(3)
        
        # 检查是否有验证码
        captcha = page.query_selector('.tencent-captcha-dy__content, [class*="captcha"]')
        if captcha:
            print("⚠️ 检测到验证码！请在浏览器中手动完成验证...")
            # 等待用户手动完成验证
            input("完成验证后按 Enter 继续...")
        
        # 4. 等待登录成功
        print("📍 步骤4: 等待登录成功...")
        page.wait_for_url('**/index.htm', timeout=30000)
        print("✅ 登录成功！")
        
        # 5. 导航到数据搬家页面
        print("📍 步骤5: 导航到数据搬家页面...")
        page.goto('https://www.dianxiaomi.com/product/dataMove/list')
        page.wait_for_load_state('networkidle')
        
        # 6. 选择速卖通数据
        print("📍 步骤6: 选择速卖通数据...")
        # 点击速卖通选项
        page.click('text=速卖通')
        time.sleep(1)
        
        # 7. 选择黄小惠店铺
        print("📍 步骤7: 选择黄小惠店铺...")
        page.click('text=黄小惠')
        time.sleep(1)
        
        # 8. 筛选未认领
        print("📍 步骤8: 筛选未认领...")
        page.click('text=未认领')
        time.sleep(2)
        
        # 9. 全选
        print("📍 步骤9: 全选产品...")
        page.click('input[type="checkbox"]')  # 全选checkbox
        time.sleep(1)
        
        # 10. 批量认领
        print("📍 步骤10: 批量认领...")
        page.click('button:has-text("批量认领")')
        time.sleep(1)
        
        # 11. 选择目标店铺PETDUNIN
        print("📍 步骤11: 选择目标店铺PETDUNIN...")
        page.click('text=速卖通')
        page.click('text=PETDUNIN')
        time.sleep(1)
        
        # 12. 确认
        print("📍 步骤12: 确认认领...")
        page.click('button:has-text("确定")')
        
        # 等待完成
        time.sleep(3)
        print("✅ 产品认领完成！")
        
        # 保存cookies
        cookies = context.cookies()
        import json
        with open('dianxiaomi_cookies.json', 'w') as f:
            json.dump(cookies, f)
        print("💾 Cookies已保存到 dianxiaomi_cookies.json")
        
        # 保持浏览器打开，方便查看结果
        input("按 Enter 关闭浏览器...")
        browser.close()

if __name__ == '__main__':
    print("=" * 50)
    print("店小秘产品认领自动化脚本")
    print("=" * 50)
    login_and_claim_products()
