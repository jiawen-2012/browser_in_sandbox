#!/usr/bin/env python3
"""
element_iframe.py - 增强版 iframe 处理脚本
结合 CDP 和 Playwright 风格，支持 iframe 内元素操作
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
    """获取页面 frame 树结构 (Playwright 风格)"""
    result = cdp_command(ws_url, "Page.getFrameTree")
    return result.get("result", {}).get("frameTree", {})


def list_frames(ws_url):
    """列出所有 frames (类似 Playwright 的 page.frames)"""
    frame_tree = get_frame_tree(ws_url)
    frames = []
    
    def traverse(tree, depth=0):
        frame = tree.get("frame", {})
        frames.append({
            "id": frame.get("id", ""),
            "parentId": frame.get("parentId"),
            "name": frame.get("name", ""),
            "url": frame.get("url", ""),
            "depth": depth
        })
        for child in tree.get("childFrames", []):
            traverse(child, depth + 1)
    
    traverse(frame_tree)
    return frames


def print_frame_tree(ws_url):
    """打印 frame 树 (Playwright 风格)"""
    frames = list_frames(ws_url)
    
    print("\n📊 Frame 树结构:")
    print("-" * 60)
    
    for frame in frames:
        indent = "  " * frame["depth"]
        name = frame["name"] or "unnamed"
        url = frame["url"][:50] + "..." if len(frame["url"]) > 50 else frame["url"]
        parent_info = f" (parent: {frame['parentId'][:20]}...)" if frame["parentId"] else " (main)"
        
        print(f"{indent}📄 {name}")
        print(f"{indent}   URL: {url}")
        print(f"{indent}   ID: {frame['id'][:30]}...{parent_info}")
    
    print(f"\n共 {len(frames)} 个 frame\n")
    return frames


def find_iframe_by_pattern(ws_url, pattern):
    """通过 URL 或 name 模式查找 iframe"""
    frames = list_frames(ws_url)
    pattern_lower = pattern.lower()
    
    for frame in frames:
        if pattern_lower in frame["url"].lower() or pattern_lower in frame["name"].lower():
            return frame
    return None


def evaluate_in_frame(ws_url, frame_id, expression):
    """在指定 frame 内执行 JavaScript (类似 Playwright 的 frame.evaluate)"""
    import websocket
    ws = websocket.create_connection(ws_url)
    
    # 先获取 frame 的 execution context
    ws.send(json.dumps({
        "id": 1,
        "method": "Page.createIsolatedWorld",
        "params": {
            "frameId": frame_id,
            "worldName": "iframe_demo"
        }
    }))
    resp = json.loads(ws.recv())
    
    # 在 frame context 中执行脚本
    ws.send(json.dumps({
        "id": 2,
        "method": "Runtime.evaluate",
        "params": {
            "expression": expression,
            "returnByValue": True
        }
    }))
    resp = json.loads(ws.recv())
    ws.close()
    
    return resp


def get_iframe_elements(ws_url, iframe_selector=None):
    """获取 iframe 内的所有元素 (Playwright 风格)"""
    
    if iframe_selector:
        # 查找指定 iframe
        frame = find_iframe_by_pattern(ws_url, iframe_selector)
        if not frame:
            print(f"未找到匹配的 iframe: {iframe_selector}")
            return []
        
        # 在 iframe 内执行
        result = evaluate_in_frame(ws_url, frame["id"], """
            (function() {
                const elements = document.querySelectorAll('input, button, a, select, textarea, [role]');
                return Array.from(elements).map(el => {
                    const rect = el.getBoundingClientRect();
                    return {
                        tag: el.tagName,
                        type: el.type || '',
                        name: el.name || '',
                        id: el.id || '',
                        placeholder: el.placeholder || '',
                        text: (el.innerText || el.textContent || '').trim().substring(0, 30),
                        role: el.getAttribute('role') || '',
                        x: Math.round(rect.left),
                        y: Math.round(rect.top),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height),
                        centerX: Math.round(rect.left + rect.width/2),
                        centerY: Math.round(rect.top + rect.height/2)
                    };
                }).filter(e => e.width > 0 && e.height > 0);
            })()
        """)
    else:
        # 在主页面执行
        result = cdp_command(ws_url, "Runtime.evaluate", {
            "expression": """
                (function() {
                    const elements = document.querySelectorAll('input, button, a, select, textarea, [role]');
                    return Array.from(elements).map(el => {
                        const rect = el.getBoundingClientRect();
                        return {
                            tag: el.tagName,
                            type: el.type || '',
                            name: el.name || '',
                            id: el.id || '',
                            placeholder: el.placeholder || '',
                            text: (el.innerText || el.textContent || '').trim().substring(0, 30),
                            role: el.getAttribute('role') || '',
                            x: Math.round(rect.left),
                            y: Math.round(rect.top),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                            centerX: Math.round(rect.left + rect.width/2),
                            centerY: Math.round(rect.top + rect.height/2)
                        };
                    }).filter(e => e.width > 0 && e.height > 0);
                })()
            """,
            "returnByValue": True
        })
    
    inner_result = result.get("result", {}).get("result", {})
    return inner_result.get("value", []) if inner_result.get("type") != "undefined" else []


def click_in_iframe(ws_url, iframe_pattern, element_text, use_js=True):
    """在 iframe 内点击元素"""
    frame = find_iframe_by_pattern(ws_url, iframe_pattern)
    if not frame:
        print(f"❌ 未找到 iframe: {iframe_pattern}")
        return False
    
    print(f"📄 找到 iframe: {frame['name'] or 'unnamed'}")
    
    # 在 iframe 内查找并点击元素
    expression = f"""
        (function() {{
            const keywords = ['{element_text}'];
            const elements = document.querySelectorAll('a, button, input, div, span');
            
            for (let el of elements) {{
                const text = (el.innerText || el.textContent || el.placeholder || '').trim();
                for (let kw of keywords) {{
                    if (text.includes(kw)) {{
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {{
                            {'el.click();' if use_js else ''}
                            return {{
                                found: true,
                                text: text.substring(0, 50),
                                x: Math.round(rect.left + rect.width/2),
                                y: Math.round(rect.top + rect.height/2),
                                tag: el.tagName
                            }};
                        }}
                    }}
                }}
            }}
            return {{found: false}};
        }})()
    """
    
    result = evaluate_in_frame(ws_url, frame["id"], expression)
    inner_result = result.get("result", {}).get("result", {})
    value = inner_result.get("value", {}) if inner_result.get("type") != "undefined" else {}
    
    if value.get("found"):
        print(f"✅ 在 iframe 内点击: '{value['text']}' ({value['tag']}) at ({value['x']}, {value['y']})")
        
        if not use_js:
            # 需要计算 iframe 在页面中的偏移
            offset_result = cdp_command(ws_url, "Runtime.evaluate", {
                "expression": f"""
                    (function() {{
                        const iframe = document.querySelector('iframe[name="{frame["name"]}"], iframe[src*="{frame["url"][:30]}"]');
                        if (iframe) {{
                            const rect = iframe.getBoundingClientRect();
                            return {{offsetX: rect.left, offsetY: rect.top}};
                        }}
                        return {{offsetX: 0, offsetY: 0}};
                    }})()
                """,
                "returnByValue": True
            })
            offset = offset_result.get("result", {}).get("result", {}).get("value", {})
            
            # 点击实际坐标
            import websocket
            ws = websocket.create_connection(ws_url)
            actual_x = value['x'] + offset.get('offsetX', 0)
            actual_y = value['y'] + offset.get('offsetY', 0)
            
            ws.send(json.dumps({
                "id": 1,
                "method": "Input.dispatchMouseEvent",
                "params": {"type": "mousePressed", "x": actual_x, "y": actual_y, "button": "left", "clickCount": 1}
            }))
            ws.recv()
            ws.send(json.dumps({
                "id": 2,
                "method": "Input.dispatchMouseEvent",
                "params": {"type": "mouseReleased", "x": actual_x, "y": actual_y, "button": "left", "clickCount": 1}
            }))
            ws.recv()
            ws.close()
        
        return True
    else:
        print(f"❌ 在 iframe 内未找到元素: {element_text}")
        return False


def type_in_iframe(ws_url, iframe_pattern, text):
    """在 iframe 的输入框内输入文本"""
    frame = find_iframe_by_pattern(ws_url, iframe_pattern)
    if not frame:
        print(f"❌ 未找到 iframe: {iframe_pattern}")
        return False
    
    # 先聚焦输入框
    result = evaluate_in_frame(ws_url, frame["id"], """
        (function() {
            const input = document.querySelector('input[type="text"], input[type="email"], input:not([type])');
            if (input) {
                input.focus();
                input.click();
                return {focused: true, placeholder: input.placeholder || ''};
            }
            return {focused: false};
        })()
    """)
    
    inner_result = result.get("result", {}).get("result", {})
    value = inner_result.get("value", {}) if inner_result.get("type") != "undefined" else {}
    
    if value.get("focused"):
        print(f"✅ 已聚焦输入框: {value.get('placeholder', 'unnamed')}")
        
        # 输入文本
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
        
        print(f"✅ 已输入文本: {text}")
        return True
    else:
        print("❌ 未找到可聚焦的输入框")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="iframe 处理脚本 (Playwright 风格)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 列出所有 frames
  python element_iframe.py --list-frames
  
  # 在指定 iframe 内查找元素
  python element_iframe.py --iframe "x-URS" --find-elements
  
  # 在 iframe 内点击元素
  python element_iframe.py --iframe "dl.reg.163.com" --click-text "登录"
  
  # 在 iframe 内输入文本
  python element_iframe.py --iframe "x-URS" --type "example@163.com"
        """
    )
    
    parser.add_argument("--port", type=int, default=18800, help="CDP端口")
    parser.add_argument("--list-frames", action="store_true", help="列出所有 frames")
    parser.add_argument("--iframe", help="iframe 选择器 (URL或name中包含的字符串)")
    parser.add_argument("--find-elements", action="store_true", help="查找 iframe 内的元素")
    parser.add_argument("--click-text", help="在 iframe 内点击包含指定文本的元素")
    parser.add_argument("--type", dest="type_text", help="在 iframe 内输入文本")
    parser.add_argument("--use-mouse", action="store_true", help="使用鼠标点击而非JS点击")
    
    args = parser.parse_args()
    
    # 获取CDP连接
    ws_url = get_cdp_url(args.port)
    if not ws_url:
        print("错误: 无法连接到浏览器CDP，请确保浏览器已启动", file=sys.stderr)
        sys.exit(1)
    
    # 执行操作
    if args.list_frames:
        print_frame_tree(ws_url)
    
    if args.iframe:
        if args.find_elements:
            print(f"\n🔍 在 iframe '{args.iframe}' 内查找元素:")
            elements = get_iframe_elements(ws_url, args.iframe)
            print(f"找到 {len(elements)} 个元素:")
            for i, el in enumerate(elements[:15]):
                tag = el.get('tag', 'unknown')
                text = el.get('text') or el.get('placeholder') or el.get('name') or ''
                role = el.get('role', '')
                x, y = el.get('centerX', 0), el.get('centerY', 0)
                print(f"  [{i+1}] [{tag}] '{text[:30]}' role={role} at ({x}, {y})")
        
        if args.click_text:
            click_in_iframe(ws_url, args.iframe, args.click_text, use_js=not args.use_mouse)
        
        if args.type_text:
            type_in_iframe(ws_url, args.iframe, args.type_text)
    elif not args.list_frames:
        parser.print_help()


if __name__ == "__main__":
    main()
