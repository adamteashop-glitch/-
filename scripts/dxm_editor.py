#!/usr/bin/env python3
"""
Dianxiaomi Editor Automation Script
使用 Playwright 解决 JavaScript 动态事件点击问题
"""

from playwright.sync_api import sync_playwright
import sys
import time

def main():
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # 打开店小秘
        print("打开店小秘...")
        page.goto("https://www.dianxiaomi.com/")
        
        # 等待登录（如果需要的话）
        input("请在浏览器中登录店小秘，完成后按回车继续...")
        
        # 导航到采集箱
        print("导航到采集箱...")
        page.goto("https://www.dianxiaomi.com/web/smt/smtProductList/draft")
        time.sleep(2)
        
        # 查找并点击编辑按钮
        print("查找编辑按钮...")
        
        # 使用 JavaScript 直接触发点击事件
        page.evaluate("""
            () => {
                // 找到所有编辑链接
                const links = document.querySelectorAll('a');
                for (let link of links) {
                    if (link.textContent.trim() === '编辑') {
                        console.log('找到编辑按钮:', link);
                        // 直接调用 onclick 处理程序
                        if (link.onclick) {
                            link.onclick();
                        }
                        // 或者触发 click 事件
                        link.click();
                        break;
                    }
                }
            }
        """)
        
        time.sleep(3)
        
        # 获取当前 URL
        print("当前 URL:", page.url)
        
        input("操作完成，按回车退出...")
        browser.close()

if __name__ == "__main__":
    main()
