#!/usr/bin/env python3
"""
element.py - CDP元素操作脚本 (V3简化版)
支持: 查找元素、点击、输入文本、截图
"""

import argparse
import json
import sys
import time
import subprocess
from urllib.request import urlopen

def get_cdp_url(port=18800):
    """获取CDP WebSocket URL"""
    try:
        with urlopen(f"http://127.0.0.1:{port}/json") as resp:
            pages = json.loads(resp.read())
            for page in pages:
                if page.get("type") == "page":
                    return page.get("webSocketDebuggerUrl")
    except Exception as e:
        print(f"无法连接CDP: {e}", file=sys.stderr)
    return None

def cdp_command(ws_url, method, params=None):
    """发送CDP命令"""
    import websocket
    ws = websocket.create_connection(ws_url)
    cmd = {"id": 1, "method": method, "params": params or {}}
    ws.send(json.dumps(cmd))
    resp = ws.recv()
    ws.close()
    return json.loads(resp)

def get_frame_tree(ws_url):
    """获取页面的 Frame 树结构（包含所有 iframe）"""
    result = cdp_command(ws_url, "Page.getFrameTree")
    return result.get("result", {}).get("frameTree", {})

def get_all_frames_content(ws_url):
    """获取主页面和所有 iframe 的内容
    
    Returns:
        {
            "mainFrame": {...},
            "frames": [
                {"frameId": "...", "url": "...", "content": {...}},
                ...
            ]
        }
    """
    # 获取 frame 树
    frame_tree = get_frame_tree(ws_url)
    main_frame = frame_tree.get("frame", {})
    
    result = {
        "mainFrame": {
            "id": main_frame.get("id"),
            "url": main_frame.get("url"),
            "title": ""
        },
        "frames": []
    }
    
    # 获取主页面内容
    main_content = get_playwright_snapshot(ws_url)
    result["mainFrame"]["title"] = main_content.get("title", "")
    result["mainFrame"]["content"] = main_content
    
    # 递归收集所有子 frame
    def collect_frames(frame_node, parent_id=None):
        frames = []
        for child in frame_node.get("childFrames", []):
            frame = child.get("frame", {})
            frame_info = {
                "frameId": frame.get("id"),
                "parentId": parent_id,
                "url": frame.get("url", ""),
                "name": frame.get("name", ""),
                "content": None
            }
            
            # 尝试获取 iframe 内容
            try:
                iframe_content = get_iframe_content(ws_url, frame.get("id"))
                frame_info["content"] = iframe_content
            except Exception as e:
                frame_info["error"] = str(e)
            
            frames.append(frame_info)
            # 递归收集子 frame
            frames.extend(collect_frames(child, frame.get("id")))
        return frames
    
    result["frames"] = collect_frames(frame_tree)
    return result

def get_iframe_content(ws_url, frame_id):
    """获取指定 iframe 的内容"""
    import websocket
    ws = websocket.create_connection(ws_url)
    
    try:
        # 创建 frame 上下文
        ws.send(json.dumps({
            "id": 1,
            "method": "Page.createIsolatedWorld",
            "params": {"frameId": frame_id, "worldName": "skill_content_extractor"}
        }))
        resp = json.loads(ws.recv())
        execution_context_id = resp.get("result", {}).get("executionContextId")
        
        if not execution_context_id:
            return {"error": "无法创建 frame 上下文"}
        
        # 在 frame 中执行内容提取
        ws.send(json.dumps({
            "id": 2,
            "method": "Runtime.evaluate",
            "params": {
                "expression": """
                    (function() {
                        function extractContent() {
                            const results = [];
                            const elements = document.querySelectorAll('input, button, a, [role], textarea, select');
                            
                            elements.forEach(el => {
                                const rect = el.getBoundingClientRect();
                                if (rect.width > 0 && rect.height > 0) {
                                    results.push({
                                        tag: el.tagName,
                                        role: el.getAttribute('role') || el.tagName.toLowerCase(),
                                        name: el.getAttribute('aria-label') || 
                                              el.getAttribute('placeholder') ||
                                              el.getAttribute('title') ||
                                              el.textContent?.trim().substring(0, 50) ||
                                              el.value?.substring(0, 50) || '',
                                        type: el.type || '',
                                        x: Math.round(rect.left),
                                        y: Math.round(rect.top),
                                        width: Math.round(rect.width),
                                        height: Math.round(rect.height),
                                        centerX: Math.round(rect.left + rect.width/2),
                                        centerY: Math.round(rect.top + rect.height/2)
                                    });
                                }
                            });
                            
                            return {
                                url: window.location.href,
                                title: document.title,
                                elements: results,
                                textContent: document.body?.innerText?.substring(0, 500) || ''
                            };
                        }
                        return extractContent();
                    })()
                """,
                "contextId": execution_context_id,
                "returnByValue": True
            }
        }))
        resp = json.loads(ws.recv())
        
        result = resp.get("result", {}).get("result", {})
        return result.get("value") if result.get("type") != "undefined" else {"error": "执行失败"}
        
    finally:
        ws.close()

def print_full_page_content(ws_url):
    """打印完整页面内容（主页面 + 所有 iframe）"""
    content = get_all_frames_content(ws_url)
    
    print("\n" + "="*70)
    print("📄 完整页面内容分析")
    print("="*70)
    
    # 主页面
    main = content.get("mainFrame", {})
    print(f"\n🌐 主页面: {main.get('title', 'Unknown')}")
    print(f"   URL: {main.get('url', 'Unknown')}")
    
    main_content = main.get("content", {})
    aria_tree = main_content.get("ariaTree", [])
    dom_tree = main_content.get("domTree", [])
    
    if aria_tree:
        print(f"\n   🌳 无障碍树: {len(aria_tree)} 个元素")
        for i, el in enumerate(aria_tree[:8]):
            role = el.get('role', 'unknown')
            name = el.get('name', '')[:30]
            print(f"      [{i+1}] [{role}] '{name}'")
    
    interactive = [e for e in dom_tree if e.get("role") in ["button", "link", "textbox", "searchbox", "input"]]
    if interactive:
        print(f"\n   🖱️  交互元素: {len(interactive)} 个")
        for i, el in enumerate(interactive[:5]):
            print(f"      [{i+1}] [{el.get('role')}] '{el.get('name', '')[:25]}'")
    
    # iframe 内容
    frames = content.get("frames", [])
    if frames:
        print(f"\n📦 发现 {len(frames)} 个 iframe:")
        
        for idx, frame in enumerate(frames, 1):
            print(f"\n   ┌─ iframe [{idx}] {frame.get('name') or 'unnamed'}")
            print(f"   │  URL: {frame.get('url', 'Unknown')[:60]}")
            
            if frame.get("error"):
                print(f"   │  ⚠️  无法访问: {frame.get('error')}")
                continue
            
            frame_content = frame.get("content", {})
            if frame_content:
                title = frame_content.get("title", "")
                elements = frame_content.get("elements", [])
                text_preview = frame_content.get("textContent", "")[:80]
                
                if title:
                    print(f"   │  标题: {title}")
                if text_preview:
                    print(f"   │  内容: {text_preview}...")
                if elements:
                    print(f"   │  元素: {len(elements)} 个")
                    # 显示关键交互元素
                    key_elements = [e for e in elements if e.get("tag") in ["INPUT", "BUTTON", "A"]]
                    for i, el in enumerate(key_elements[:4]):
                        tag = el.get("tag", "")
                        name = el.get("name", "")[:20]
                        el_type = el.get("type", "")
                        info = f"{tag}" + (f"[{el_type}]" if el_type else "")
                        print(f"   │    [{i+1}] {info}: '{name}'")
                    if len(key_elements) > 4:
                        print(f"   │    ... 还有 {len(key_elements) - 4} 个")
            print(f"   └─")
    
    print("\n" + "="*70)
    return content

def get_playwright_snapshot(ws_url):
    """获取 Playwright 格式的页面快照（DOM树 + 无障碍树）"""
    result = cdp_command(ws_url, "Runtime.evaluate", {
        "expression": """
            (function() {
                function buildAriaTree(element, depth = 0) {
                    const results = [];
                    if (!element || depth > 10) return results;
                    
                    const role = element.getAttribute('role') || 
                                element.tagName.toLowerCase();
                    const name = element.getAttribute('aria-label') || 
                                element.getAttribute('placeholder') ||
                                element.getAttribute('title') ||
                                element.textContent?.trim().substring(0, 50) || '';
                    const rect = element.getBoundingClientRect();
                    
                    if (rect.width > 0 && rect.height > 0 && 
                        rect.top >= 0 && rect.left >= 0 &&
                        (name || ['button', 'a', 'input', 'select', 'textarea'].includes(element.tagName.toLowerCase()))) {
                        results.push({
                            role: role,
                            name: name,
                            tag: element.tagName,
                            x: Math.round(rect.left),
                            y: Math.round(rect.top),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                            centerX: Math.round(rect.left + rect.width/2),
                            centerY: Math.round(rect.top + rect.height/2),
                            depth: depth
                        });
                    }
                    
                    for (let child of element.children) {
                        results.push(...buildAriaTree(child, depth + 1));
                    }
                    return results;
                }
                
                // 优先使用无障碍树，回退到DOM树
                const ariaElements = buildAriaTree(document.body);
                
                // 同时获取普通DOM元素作为补充
                const domElements = Array.from(document.querySelectorAll('a, button, input, select, textarea, [role]'))
                    .map(el => {
                        const rect = el.getBoundingClientRect();
                        return {
                            role: el.getAttribute('role') || el.tagName.toLowerCase(),
                            name: el.getAttribute('aria-label') || 
                                  el.getAttribute('placeholder') ||
                                  el.getAttribute('title') ||
                                  el.textContent?.trim().substring(0, 50) || '',
                            tag: el.tagName,
                            x: Math.round(rect.left),
                            y: Math.round(rect.top),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                            centerX: Math.round(rect.left + rect.width/2),
                            centerY: Math.round(rect.top + rect.height/2),
                            source: 'dom'
                        };
                    })
                    .filter(el => el.width > 0 && el.height > 0 && el.y >= 0);
                
                return {
                    ariaTree: ariaElements,
                    domTree: domElements,
                    title: document.title,
                    url: window.location.href
                };
            })()
        """,
        "returnByValue": True
    })
    
    inner_result = result.get("result", {}).get("result", {})
    snapshot = inner_result.get("value") if inner_result.get("type") != "undefined" else None
    return snapshot or {"ariaTree": [], "domTree": [], "title": "", "url": ""}

def find_elements(ws_url, keywords):
    """查找包含指定文本的元素 - 优先使用Playwright风格的无障碍树"""
    snapshot = get_playwright_snapshot(ws_url)
    
    # 优先搜索无障碍树
    all_elements = snapshot.get("ariaTree", []) + snapshot.get("domTree", [])
    
    matched = []
    for el in all_elements:
        name = el.get("name", "").lower()
        role = el.get("role", "").lower()
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in name or kw_lower in role:
                matched.append(el)
                break
    
    # 去重（基于位置和大小）
    seen = set()
    unique = []
    for el in matched:
        key = f"{el.get('x')},{el.get('y')},{el.get('width')},{el.get('height')}"
        if key not in seen:
            seen.add(key)
            unique.append(el)
    
    if unique:
        print(f"找到 {len(unique)} 个匹配元素 (关键词: {keywords}):")
        for i, el in enumerate(unique[:8]):
            role = el.get('role', 'unknown')
            name = el.get('name', '')[:40]
            x, y = el.get('centerX', el.get('x', 0)), el.get('centerY', el.get('y', 0))
            print(f"  [{i+1}] [{role}] '{name}' at ({x}, {y})")
    else:
        print(f"未找到匹配元素 (关键词: {keywords})")
        # 回退到原始方法
        return find_elements_legacy(ws_url, keywords)
    
    return unique

def find_elements_legacy(ws_url, keywords):
    """原始查找方法（回退）"""
    result = cdp_command(ws_url, "Runtime.evaluate", {
        "expression": f"""
            Array.from(document.querySelectorAll('*'))
                .filter(el => el.textContent && ({' || '.join([f'el.textContent.includes("{k}")' for k in keywords])}))
                .map(el => {{
                    const rect = el.getBoundingClientRect();
                    return {{
                        tag: el.tagName,
                        text: el.textContent.trim().substring(0, 50),
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height),
                        centerX: Math.round(rect.x + rect.width/2),
                        centerY: Math.round(rect.y + rect.height/2)
                    }};
                }})
        """,
        "returnByValue": True
    })
    
    inner_result = result.get("result", {}).get("result", {})
    elements = inner_result.get("value", []) if inner_result.get("type") == "object" else []
    if elements:
        print(f"[Legacy] 找到 {len(elements)} 个匹配元素:")
        for i, el in enumerate(elements[:5]):
            print(f"  [{i+1}] {el.get('tag')}: '{el.get('text')}' at ({el.get('centerX', 0)}, {el.get('centerY', 0)})")
    else:
        print("未找到匹配元素")
    return elements

def click_at(ws_url, x, y):
    """在指定坐标点击"""
    import websocket
    ws = websocket.create_connection(ws_url)
    
    # 鼠标按下
    ws.send(json.dumps({
        "id": 1,
        "method": "Input.dispatchMouseEvent",
        "params": {"type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": 1}
    }))
    ws.recv()
    
    # 鼠标释放
    ws.send(json.dumps({
        "id": 2,
        "method": "Input.dispatchMouseEvent",
        "params": {"type": "mouseReleased", "x": x, "y": y, "button": "left", "clickCount": 1}
    }))
    ws.recv()
    ws.close()
    
    print(f"点击坐标: ({x}, {y})")
    return True

def click_element_by_text(ws_url, text, use_js=False):
    """点击包含指定文本的元素 - 优先使用Playwright风格的无障碍树定位
    
    Args:
        ws_url: CDP WebSocket URL
        text: 要点击的元素文本
        use_js: 是否使用JavaScript点击（绕过部分反爬检测）
    """
    # 首先尝试使用Playwright风格的无障碍树查找
    snapshot = get_playwright_snapshot(ws_url)
    all_elements = snapshot.get("ariaTree", []) + snapshot.get("domTree", [])
    
    text_lower = text.lower()
    target = None
    
    # 优先匹配无障碍标签（aria-label等）
    for el in all_elements:
        name = el.get("name", "").lower()
        role = el.get("role", "").lower()
        if text_lower in name or text_lower in role:
            target = el
            break
    
    if target:
        x = target.get("centerX", target.get("x", 0))
        y = target.get("centerY", target.get("y", 0))
        role = target.get("role", "unknown")
        name = target.get("name", "")[:30]
        
        if use_js:
            # 使用JavaScript点击（更可靠）
            result = cdp_command(ws_url, "Runtime.evaluate", {
                "expression": f"""
                    (function() {{
                        var elements = document.querySelectorAll('[role], button, a, input');
                        for (var i = 0; i < elements.length; i++) {{
                            var el = elements[i];
                            var rect = el.getBoundingClientRect();
                            if (Math.abs(rect.left + rect.width/2 - {x}) < 5 && 
                                Math.abs(rect.top + rect.height/2 - {y}) < 5) {{
                                el.click();
                                return {{clicked: true}};
                            }}
                        }}
                        // 回退：在坐标处触发点击
                        document.elementFromPoint({x}, {y})?.click();
                        return {{clicked: true, method: 'coordinate'}};
                    }})()
                """,
                "returnByValue": True
            })
            print(f"JS点击成功: [{role}] '{name}' at ({x}, {y})")
        else:
            # 使用CDP鼠标事件点击
            click_at(ws_url, x, y)
            print(f"点击元素: [{role}] '{name}' at ({x}, {y})")
        return True
    
    # 无障碍树未找到，回退到传统方法
    print(f"无障碍树未找到 '{text}'，回退到DOM查找...")
    return click_element_by_text_legacy(ws_url, text, use_js)

def click_element_by_text_legacy(ws_url, text, use_js=False):
    """传统点击方法（回退）"""
    if use_js:
        result = cdp_command(ws_url, "Runtime.evaluate", {
            "expression": f"""
                (function() {{
                    var keywords = ['{text}'];
                    var elements = document.querySelectorAll('a, button, div, span');
                    for (var i = 0; i < elements.length; i++) {{
                        var el = elements[i];
                        var elText = (el.innerText || el.textContent || '').trim();
                        for (var j = 0; j < keywords.length; j++) {{
                            if (elText === keywords[j] || elText.includes(keywords[j])) {{
                                var rect = el.getBoundingClientRect();
                                if (rect.width > 0 && rect.height > 0 && rect.top > 0 && rect.left > 0) {{
                                    el.click();
                                    return {{
                                        text: elText.substring(0, 50),
                                        x: Math.round(rect.left + rect.width/2),
                                        y: Math.round(rect.top + rect.height/2),
                                        clicked: true
                                    }};
                                }}
                            }}
                        }}
                    }}
                    return {{clicked: false, reason: 'element not found'}};
                }})()
            """,
            "returnByValue": True
        })
        
        inner_result = result.get("result", {}).get("result", {})
        value = inner_result.get("value") if inner_result.get("type") != "undefined" else None
        if value and value.get('clicked'):
            print(f"[Legacy] JS点击成功: '{value['text']}' at ({int(value['x'])}, {int(value['y'])})")
            return True
        else:
            print(f"[Legacy] JS点击失败: {value}")
            return False
    else:
        result = cdp_command(ws_url, "Runtime.evaluate", {
            "expression": f"""
                (function() {{
                    const el = Array.from(document.querySelectorAll('*'))
                        .find(e => e.textContent && e.textContent.trim().includes('{text}'));
                    if (el) {{
                        const rect = el.getBoundingClientRect();
                        el.click();
                        return {{x: rect.left + rect.width/2, y: rect.top + rect.height/2}};
                    }}
                    return null;
                }})()
            """,
            "returnByValue": True
        })
        
        inner_result = result.get("result", {}).get("result", {})
        pos = inner_result.get("value") if inner_result.get("type") != "undefined" else None
        if pos:
            print(f"[Legacy] 点击元素 '{text}' 在 ({int(pos['x'])}, {int(pos['y'])})")
            return True
        else:
            print(f"未找到元素 '{text}'")
            return False

def type_text(ws_url, text):
    """输入文本"""
    import websocket
    ws = websocket.create_connection(ws_url)
    
    for char in text:
        ws.send(json.dumps({
            "id": 1,
            "method": "Input.dispatchKeyEvent",
            "params": {"type": "char", "text": char}
        }))
        ws.recv()
        time.sleep(0.01)
    
    ws.close()
    print(f"输入文本: {text}")
    return True

def screenshot(ws_url, output_path, display=99):
    """截图"""
    # 先尝试CDP截图
    result = cdp_command(ws_url, "Page.captureScreenshot")
    data = result.get("result", {}).get("data")
    
    if data:
        import base64
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(data))
        print(f"截图已保存: {output_path}")
        return True
    
    # CDP失败，回退到Xvfb截图
    print("CDP截图失败，使用Xvfb截图...")
    try:
        subprocess.run(
            ["import", "-window", "root", output_path],
            env={"DISPLAY": f":{display}"},
            check=True
        )
        print(f"截图已保存: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"截图失败: {e}", file=sys.stderr)
        return False

def print_snapshot(ws_url):
    """打印Playwright风格的页面快照"""
    snapshot = get_playwright_snapshot(ws_url)
    
    print(f"\n📄 页面: {snapshot.get('title', 'Unknown')}")
    print(f"🔗 URL: {snapshot.get('url', 'Unknown')}\n")
    
    # 打印无障碍树
    aria_tree = snapshot.get("ariaTree", [])
    if aria_tree:
        print(f"🌳 无障碍树 ({len(aria_tree)} 个元素):")
        for i, el in enumerate(aria_tree[:15]):  # 只显示前15个
            indent = "  " * min(el.get("depth", 0), 3)
            role = el.get("role", "unknown")
            name = el.get("name", "")[:30]
            x, y = el.get("centerX", 0), el.get("centerY", 0)
            print(f"{indent}[{i+1}] [{role}] '{name}' ({x}, {y})")
        if len(aria_tree) > 15:
            print(f"  ... 还有 {len(aria_tree) - 15} 个元素")
    
    # 打印DOM交互元素
    dom_tree = snapshot.get("domTree", [])
    interactive = [e for e in dom_tree if e.get("role") in ["button", "link", "textbox", "searchbox"]]
    if interactive:
        print(f"\n🖱️  交互元素 ({len(interactive)} 个):")
        for i, el in enumerate(interactive[:10]):
            role = el.get("role", "unknown")
            name = el.get("name", "")[:25]
            x, y = el.get("centerX", 0), el.get("centerY", 0)
            print(f"  [{i+1}] [{role}] '{name}' ({x}, {y})")
    
    print("")

def main():
    parser = argparse.ArgumentParser(description="CDP元素操作 (Playwright风格)")
    parser.add_argument("--port", type=int, default=18800, help="CDP端口")
    parser.add_argument("--find", help="查找元素关键词(逗号分隔)")
    parser.add_argument("--click", nargs=2, type=int, metavar=("X", "Y"), help="点击坐标")
    parser.add_argument("--click-text", help="点击包含指定文本的元素")
    parser.add_argument("--js-click", action="store_true", help="使用JavaScript点击（绕过反爬检测，更可靠）")
    parser.add_argument("--type", dest="type_text", help="输入文本")
    parser.add_argument("--screenshot", help="截图保存路径")
    parser.add_argument("--display", type=int, default=99, help="Xvfb显示号")
    parser.add_argument("--snapshot", action="store_true", help="打印Playwright风格的页面快照")
    parser.add_argument("--full-content", action="store_true", help="打印完整页面内容（主页面 + 所有iframe）")
    
    args = parser.parse_args()
    
    # 获取CDP连接
    ws_url = get_cdp_url(args.port)
    if not ws_url:
        print("错误: 无法连接到浏览器CDP，请确保浏览器已启动", file=sys.stderr)
        sys.exit(1)
    
    # 执行操作
    if args.full_content:
        print_full_page_content(ws_url)
    elif args.snapshot:
        print_snapshot(ws_url)
    
    if args.find:
        keywords = [k.strip() for k in args.find.split(",")]
        find_elements(ws_url, keywords)
    
    if args.click:
        click_at(ws_url, args.click[0], args.click[1])
    
    if args.click_text:
        click_element_by_text(ws_url, args.click_text, use_js=args.js_click)
    
    if args.type_text:
        type_text(ws_url, args.type_text)
    
    if args.screenshot:
        screenshot(ws_url, args.screenshot, args.display)

if __name__ == "__main__":
    main()
