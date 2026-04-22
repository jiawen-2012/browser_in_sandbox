#!/usr/bin/env python3
"""
Playwright iframe 处理完整示例
演示各种 iframe 场景的操作方法
"""

import asyncio
import json
from playwright.async_api import async_playwright, Page, Frame, FrameLocator


class PlaywrightIframeDemo:
    """Playwright iframe 操作演示类"""
    
    def __init__(self, page: Page):
        self.page = page
    
    async def analyze_frames(self):
        """分析页面所有 iframe"""
        print("\n" + "="*70)
        print("📊 iframe 分析方法对比")
        print("="*70)
        
        # 方法1: 通过 main_frame 递归遍历
        print("\n【方法1】递归遍历 frame 树:")
        await self._dump_frame_tree(self.page.main_frame)
        
        # 方法2: 获取所有 frames 列表
        print(f"\n【方法2】page.frames 列表 (共 {len(self.page.frames)} 个):")
        for i, frame in enumerate(self.page.frames):
            name = frame.name or "unnamed"
            url = frame.url[:50] + "..." if len(frame.url) > 50 else frame.url
            parent = frame.parent_frame
            parent_info = f" (parent: {parent.name})" if parent else " (main frame)"
            print(f"  [{i}] {name}: {url}{parent_info}")
    
    async def _dump_frame_tree(self, frame: Frame, indent=""):
        """递归打印 frame 树"""
        name = frame.name or "unnamed"
        url = frame.url[:60] + "..." if len(frame.url) > 60 else frame.url
        print(f"{indent}📄 {name}")
        print(f"{indent}   URL: {url}")
        
        for child in frame.child_frames:
            await self._dump_frame_tree(child, indent + "  ")
    
    async def scenario_1_basic_iframe_access(self):
        """场景1: 基本 iframe 访问 - 通过 frame_locator"""
        print("\n" + "="*70)
        print("🎯 场景1: 基本 iframe 访问 (frame_locator)")
        print("="*70)
        
        # 进入 id 以 x-URS-iframe 开头的 iframe
        try:
            login_frame = self.page.frame_locator('iframe[id^="x-URS-iframe"]')
            
            # 在 iframe 内查找邮箱输入框
            email_input = login_frame.locator('input[placeholder*="邮箱"], input[placeholder*="手机号"]').first
            await email_input.wait_for(state="visible", timeout=5000)
            
            print("  ✅ 成功进入登录 iframe")
            print(f"  📍 找到邮箱输入框")
            
            # 获取元素信息
            placeholder = await email_input.get_attribute("placeholder")
            input_type = await email_input.get_attribute("type")
            print(f"     placeholder: {placeholder}")
            print(f"     type: {input_type}")
            
        except Exception as e:
            print(f"  ❌ 失败: {e}")
    
    async def scenario_2_frame_object_access(self):
        """场景2: 通过 Frame 对象直接访问"""
        print("\n" + "="*70)
        print("🎯 场景2: Frame 对象直接访问")
        print("="*70)
        
        # 遍历所有 frames 找到目标
        target_frame = None
        for frame in self.page.frames:
            if "dl.reg.163.com" in frame.url or frame.name.startswith("x-URS"):
                target_frame = frame
                break
        
        if not target_frame:
            print("  ❌ 未找到目标 frame")
            return
        
        print(f"  ✅ 找到目标 frame: {target_frame.name or 'unnamed'}")
        
        # 在 frame 内执行 JavaScript
        result = await target_frame.evaluate("""
            () => {
                const inputs = document.querySelectorAll('input');
                return {
                    count: inputs.length,
                    inputs: Array.from(inputs).slice(0, 5).map(i => ({
                        type: i.type,
                        placeholder: i.placeholder,
                        name: i.name
                    }))
                };
            }
        """)
        
        print(f"  📋 iframe 内找到 {result['count']} 个输入框")
        for inp in result['inputs']:
            print(f"     - type={inp['type']}, placeholder={inp['placeholder']}")
    
    async def scenario_3_nested_iframes(self):
        """场景3: 嵌套 iframe 处理"""
        print("\n" + "="*70)
        print("🎯 场景3: 嵌套 iframe 处理")
        print("="*70)
        
        # 检查是否有嵌套 iframe
        nested_found = False
        for frame in self.page.frames:
            if len(frame.child_frames) > 0:
                nested_found = True
                print(f"  📁 Frame '{frame.name}' 有 {len(frame.child_frames)} 个子 iframe:")
                for child in frame.child_frames:
                    print(f"     └─ {child.name or 'unnamed'}: {child.url[:40]}...")
        
        if not nested_found:
            print("  ℹ️  当前页面没有嵌套 iframe")
        
        # 演示如何进入嵌套 iframe（如果有的话）
        print("\n  💡 嵌套 iframe 进入方法:")
        print("     page.frame_locator('#outer-iframe').frame_locator('#inner-iframe')")
    
    async def scenario_4_cross_origin_iframe(self):
        """场景4: 跨域 iframe 处理"""
        print("\n" + "="*70)
        print("🎯 场景4: 跨域 iframe 处理")
        print("="*70)
        
        # 分析哪些 frame 是跨域的
        main_origin = self.page.url.split('/')[2] if self.page.url else ""
        
        print(f"  🌐 主页面 origin: {main_origin}")
        print("\n  Frame 跨域分析:")
        
        for frame in self.page.frames:
            frame_origin = frame.url.split('/')[2] if frame.url else ""
            is_cross_origin = frame_origin != main_origin and frame_origin != ""
            status = "🔒 跨域" if is_cross_origin else "✅ 同域"
            name = frame.name or "unnamed"
            print(f"     {name}: {frame_origin} {status}")
        
        print("\n  💡 Playwright 自动处理跨域，无需额外配置")
    
    async def scenario_5_dynamic_iframe_wait(self):
        """场景5: 动态加载 iframe 的等待处理"""
        print("\n" + "="*70)
        print("🎯 场景5: 动态 iframe 等待")
        print("="*70)
        
        print("  ⏳ 等待 iframe 加载...")
        
        # 方法1: 等待 iframe 元素出现在 DOM 中
        try:
            await self.page.wait_for_selector('iframe[id^="x-URS-iframe"]', state="attached", timeout=10000)
            print("  ✅ iframe 元素已加载")
        except Exception as e:
            print(f"  ❌ 等待失败: {e}")
        
        # 方法2: 等待 frame 事件
        print("\n  📡 Frame 事件监听示例:")
        print("     page.on('frameattached', handler)")
        print("     page.on('framenavigated', handler)")
        print("     page.on('framedetached', handler)")
    
    async def scenario_6_iframe_form_interaction(self):
        """场景6: iframe 内表单交互"""
        print("\n" + "="*70)
        print("🎯 场景6: iframe 内表单交互")
        print("="*70)
        
        try:
            # 进入登录 iframe
            login_frame = self.page.frame_locator('iframe[id^="x-URS-iframe"]')
            
            # 填写邮箱（演示，不真填）
            email_input = login_frame.locator('input[placeholder*="邮箱"]').first
            await email_input.wait_for(state="visible")
            
            # 获取输入框位置信息
            box = await email_input.bounding_box()
            if box:
                print(f"  📍 邮箱输入框位置: x={box['x']:.0f}, y={box['y']:.0f}")
                print(f"     尺寸: {box['width']:.0f}x{box['height']:.0f}")
            
            # 查找密码框
            pwd_input = login_frame.locator('input[type="password"]').first
            if await pwd_input.is_visible():
                print("  ✅ 找到密码输入框")
            
            # 查找登录按钮
            login_btn = login_frame.locator('a:has-text("登录"), #dologin').first
            if await login_btn.is_visible():
                text = await login_btn.text_content()
                print(f"  ✅ 找到登录按钮: '{text.strip()}'")
            
            print("\n  💡 实际填写方法:")
            print("     await email_input.fill('your@email.com')")
            print("     await pwd_input.fill('yourpassword')")
            print("     await login_btn.click()")
            
        except Exception as e:
            print(f"  ❌ 失败: {e}")
    
    async def scenario_7_iframe_to_parent_communication(self):
        """场景7: iframe 与父页面通信"""
        print("\n" + "="*70)
        print("🎯 场景7: iframe 与父页面通信")
        print("="*70)
        
        print("  📤 从父页面向 iframe 发送数据:")
        print("     await frame.evaluate('window.myData = {key: \"value\"}')")
        
        print("\n  📥 从 iframe 获取数据:")
        print("     data = await frame.evaluate('window.myData')")
        
        print("\n  🔄 父页面调用 iframe 函数:")
        print("     result = await frame.evaluate('() => myFunction()')")
        
        # 实际演示
        target_frame = None
        for frame in self.page.frames:
            if "dl.reg.163.com" in frame.url:
                target_frame = frame
                break
        
        if target_frame:
            # 在 iframe 内设置数据
            await target_frame.evaluate('window.demoData = {source: "playwright", time: Date.now()}')
            
            # 读取数据
            data = await target_frame.evaluate('window.demoData')
            print(f"\n  ✅ 演示成功: {json.dumps(data, indent=2)}")
    
    async def scenario_8_iframe_screenshot(self):
        """场景8: iframe 截图"""
        print("\n" + "="*70)
        print("🎯 场景8: iframe 截图")
        print("="*70)
        
        try:
            # 对整个页面截图
            await self.page.screenshot(path="/tmp/163_full.png", full_page=True)
            print("  ✅ 完整页面截图: /tmp/163_full.png")
            
            # 对特定 iframe 截图（通过 locator）
            login_frame = self.page.frame_locator('iframe[id^="x-URS-iframe"]')
            frame_element = login_frame.locator(':scope')  # 获取 iframe 元素本身
            
            # 先定位到 iframe 元素，然后截图
            iframe_loc = self.page.locator('iframe[id^="x-URS-iframe"]')
            await iframe_loc.screenshot(path="/tmp/163_iframe.png")
            print("  ✅ iframe 截图: /tmp/163_iframe.png")
            
        except Exception as e:
            print(f"  ⚠️ 截图部分失败: {e}")
    
    async def run_all_scenarios(self):
        """运行所有场景"""
        await self.analyze_frames()
        await self.scenario_1_basic_iframe_access()
        await self.scenario_2_frame_object_access()
        await self.scenario_3_nested_iframes()
        await self.scenario_4_cross_origin_iframe()
        await self.scenario_5_dynamic_iframe_wait()
        await self.scenario_6_iframe_form_interaction()
        await self.scenario_7_iframe_to_parent_communication()
        await self.scenario_8_iframe_screenshot()


async def main():
    """主函数"""
    async with async_playwright() as p:
        print("🚀 启动浏览器...")
        
        # 启动有头浏览器
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        # 设置事件监听
        page.on("frameattached", lambda f: print(f"\n📎 Frame attached: {f.name or 'unnamed'}"))
        page.on("framenavigated", lambda f: print(f"\n🔄 Frame navigated: {f.name or 'unnamed'}"))
        
        # 访问 163 邮箱
        print("🌐 访问 163 邮箱...")
        await page.goto("https://mail.163.com", wait_until="networkidle")
        await asyncio.sleep(2)  # 等待 iframe 完全加载
        
        # 运行所有演示场景
        demo = PlaywrightIframeDemo(page)
        await demo.run_all_scenarios()
        
        print("\n" + "="*70)
        print("✅ 所有场景演示完成")
        print("="*70)
        
        # 等待观察
        print("\n⏳ 等待 3 秒后关闭...")
        await asyncio.sleep(3)
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
