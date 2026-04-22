#!/usr/bin/env python3
"""
Playwright iframe 处理示例脚本
演示如何遍历 iframe 树、进入 iframe 操作元素
"""

import asyncio
from playwright.async_api import async_playwright


async def dump_frame_tree(frame, indent=""):
    """递归遍历并打印 frame 树结构"""
    name = frame.name or "unnamed"
    url = frame.url[:60] + "..." if len(frame.url) > 60 else frame.url
    print(f"{indent}📄 {name}")
    print(f"{indent}   URL: {url}")
    
    for child in frame.child_frames:
        await dump_frame_tree(child, indent + "  ")


async def analyze_page_frames(page):
    """分析页面的所有 iframe"""
    print("\n" + "="*60)
    print("📊 页面 Frame 分析")
    print("="*60)
    
    # 方式1: 从 main_frame 递归遍历
    print("\n【方式1】从 main_frame 递归遍历:")
    await dump_frame_tree(page.main_frame)
    
    # 方式2: 获取所有 frames 列表
    print(f"\n【方式2】page.frames 列表 (共 {len(page.frames)} 个):")
    for i, frame in enumerate(page.frames):
        name = frame.name or "unnamed"
        url = frame.url[:50] + "..." if len(frame.url) > 50 else frame.url
        print(f"  [{i}] {name}: {url}")


async def operate_in_iframe(page):
    """在 iframe 内操作元素"""
    print("\n" + "="*60)
    print("🎯 iframe 元素操作")
    print("="*60)
    
    # 方式1: 使用 frame_locator 进入 iframe
    print("\n【方式1】使用 frame_locator 进入登录 iframe:")
    
    # 定位登录 iframe (id 以 x-URS-iframe 开头)
    login_frame = page.frame_locator('iframe[id^="x-URS-iframe"]')
    
    # 在 iframe 内查找输入框
    try:
        # 查找邮箱输入框
        email_input = login_frame.locator('input[placeholder*="邮箱"], input[placeholder*="手机号"]')
        await email_input.wait_for(state="visible", timeout=5000)
        print("  ✅ 找到邮箱/手机号输入框")
        
        # 获取输入框信息
        input_type = await email_input.get_attribute("type")
        placeholder = await email_input.get_attribute("placeholder")
        print(f"     type={input_type}, placeholder={placeholder}")
        
    except Exception as e:
        print(f"  ❌ 未找到邮箱输入框: {e}")
    
    # 查找密码输入框
    try:
        pwd_input = login_frame.locator('input[type="password"]').first
        await pwd_input.wait_for(state="visible", timeout=3000)
        print("  ✅ 找到密码输入框")
    except Exception as e:
        print(f"  ❌ 未找到密码输入框: {e}")
    
    # 方式2: 通过 frame 对象直接操作
    print("\n【方式2】通过 frame 对象操作:")
    
    # 获取指定 name 或 url 的 frame
    target_frame = None
    for frame in page.frames:
        if "dl.reg.163.com" in frame.url:
            target_frame = frame
            break
    
    if target_frame:
        print(f"  ✅ 找到目标 frame: {frame.name or 'unnamed'}")
        
        # 在 frame 内执行 JavaScript
        result = await target_frame.evaluate("""
            () => {
                const inputs = document.querySelectorAll('input');
                return Array.from(inputs).map(i => ({
                    type: i.type,
                    placeholder: i.placeholder,
                    name: i.name
                }));
            }
        """)
        print(f"  📋 iframe 内找到 {len(result)} 个输入框:")
        for inp in result[:5]:  # 只显示前5个
            print(f"     - type={inp['type']}, placeholder={inp['placeholder']}")
    else:
        print("  ❌ 未找到目标 frame")


async def fill_login_form(page, email=None, password=None):
    """填写登录表单（实际填写）"""
    print("\n" + "="*60)
    print("📝 填写登录表单")
    print("="*60)
    
    try:
        # 进入登录 iframe
        login_frame = page.frame_locator('iframe[id^="x-URS-iframe"]')
        
        # 填写邮箱
        if email:
            email_input = login_frame.locator('input[placeholder*="邮箱"], input[placeholder*="手机号"]').first
            await email_input.fill(email)
            print(f"  ✅ 已填写邮箱: {email}")
        
        # 填写密码
        if password:
            pwd_input = login_frame.locator('input[type="password"]').first
            await pwd_input.fill(password)
            print(f"  ✅ 已填写密码: {'*' * len(password)}")
        
        # 查找登录按钮
        login_btn = login_frame.locator('a:has-text("登录"), button:has-text("登录"), #dologin').first
        if await login_btn.is_visible():
            print("  ✅ 找到登录按钮")
            # await login_btn.click()  # 暂不点击
        
    except Exception as e:
        print(f"  ❌ 填写失败: {e}")


async def main():
    """主函数"""
    async with async_playwright() as p:
        # 启动浏览器
        # 注意: 如果在无显示器环境运行，需要设置 headless=True 或使用 xvfb-run
        import os
        headless = os.environ.get('DISPLAY') is None
        if headless:
            print("⚠️  未检测到 DISPLAY，使用 headless 模式")
        
        browser = await p.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        # 监听 frame 事件
        page.on("frameattached", lambda frame: print(f"📎 Frame attached: {frame.name or 'unnamed'}"))
        page.on("framenavigated", lambda frame: print(f"🔄 Frame navigated: {frame.name or 'unnamed'} -> {frame.url[:40]}..."))
        page.on("framedetached", lambda frame: print(f"✂️ Frame detached: {frame.name or 'unnamed'}"))
        
        # 访问 163 邮箱
        print("🌐 正在打开 163 邮箱...")
        await page.goto("https://mail.163.com", wait_until="networkidle")
        await asyncio.sleep(2)  # 等待 iframe 加载
        
        # 分析页面 frames
        await analyze_page_frames(page)
        
        # 操作 iframe 内元素
        await operate_in_iframe(page)
        
        # 填写登录表单（可选）
        # await fill_login_form(page, email="test@163.com", password="123456")
        
        # 截图保存
        await page.screenshot(path="/tmp/163_playwright.png", full_page=True)
        print("\n📸 截图已保存: /tmp/163_playwright.png")
        
        # 等待观察
        print("\n⏳ 等待 5 秒后关闭...")
        await asyncio.sleep(5)
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
