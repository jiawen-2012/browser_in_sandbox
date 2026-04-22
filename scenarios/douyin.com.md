---
domain: douyin.com
aliases: [抖音, 抖音网页版]
updated: 2026-04-13
---

# 抖音自动化场景

## 快速开始（推荐）

```bash
# 1. 启动浏览器打开抖音
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/browser.sh start "https://www.douyin.com"

# 2. 等待页面加载（抖音加载较慢，建议等待5秒以上）
sleep 5

# 3. 截图查看当前状态
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --screenshot /tmp/douyin_status.png
```

## 单标签页模式（浏览内容）

适用于：查看视频、浏览推荐内容，不需要登录

```bash
# 启动并截图查看
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/browser.sh start "https://www.douyin.com"
sleep 5
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --screenshot /tmp/douyin_browse.png
```

**实际经验：**
- 抖音页面使用大量动态加载和Canvas渲染，`--find` 命令可能找不到元素
- 建议直接截图查看页面状态，而不是依赖元素查找
- 页面加载时间约 3-5 秒，网络慢时可能需要更久

## 双标签页模式（登录操作）

### 为什么需要双标签页？

抖音网页版会触发系统级的外部协议调用（`douyin://`），导致浏览器弹出"是否打开抖音App"的提示。这个弹窗会干扰后续自动化操作。

**双标签页策略的核心思路：**

```
标签页1（诱饵页）：打开抖音 → 触发弹窗 → 被弹窗干扰（放弃使用）
         ↓
标签页2（工作页）：新标签页打开抖音 → 弹窗已在标签页1触发过 → 干净无干扰
```

**原理说明：**
- 抖音的协议唤起机制通常只在页面首次加载时触发一次
- 第一个标签页作为"诱饵"承担弹窗干扰
- 第二个标签页由于协议唤起已被触发过，不会再弹出提示
- 所有实际操作都在第二个标签页执行

### 操作流程

```bash
# === 标签页1: 诱饵页（承担弹窗干扰）===

# 1. 启动浏览器打开抖音（诱饵页）
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/browser.sh start "https://www.douyin.com"
sleep 5

# 2. 截图确认页面状态（此时可能已有弹窗）
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --screenshot /tmp/douyin_tab1.png

# 3. 尝试点击登录按钮（触发弹窗）
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --click 1700 100

# === 标签页2: 工作页（实际操作）===

# 4. 通过CDP创建新标签页
cd ~/.openclaw/workspace/skills/headed-browser-open-v3/scripts && python3 << 'PYEOF'
import websocket, json, urllib.request
response = urllib.request.urlopen('http://127.0.0.1:18800/json/list', timeout=5)
pages = json.loads(response.read().decode())
ws_url = pages[0]['webSocketDebuggerUrl']
ws = websocket.create_connection(ws_url, timeout=15)
ws.send(json.dumps({'id': 1, 'method': 'Target.createTarget', 'params': {'url': 'https://www.douyin.com'}}))
while True:
    msg = json.loads(ws.recv())
    if msg.get('id') == 1:
        print(f"新标签页创建成功: {msg.get('result', {}).get('targetId')}")
        break
ws.close()
PYEOF

sleep 3

# 5. 在标签页2中执行实际操作（此时无弹窗干扰）
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --screenshot /tmp/douyin_tab2.png
# ... 执行登录、输入手机号等操作
```

### 关键要点

| 标签页 | 用途 | 状态 |
|--------|------|------|
| 标签页1 | 诱饵页，触发并承担弹窗干扰 | 有弹窗，不用于实际操作 |
| 标签页2 | 工作页，执行所有自动化操作 | 干净，无弹窗干扰 |

**注意事项：**
- 标签页1仅作为诱饵，截图记录即可，不执行关键操作
- 所有实际登录、输入、点击操作都在标签页2执行
- 如果标签页2仍出现弹窗，可能需要先关闭标签页1再操作

## 获取视频信息

```bash
# 打开具体视频页面
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/browser.sh start "https://www.douyin.com/video/xxxxxx"
sleep 5

# 截图查看视频信息
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --screenshot /tmp/douyin_video.png
```

## 平台特征

| 特征 | 说明 |
|------|------|
| 渲染方式 | 大量使用 Canvas 和动态加载 |
| 反爬强度 | 高，频繁操作会触发验证 |
| 元素查找 | `--find` 通常无法找到元素 |
| 推荐策略 | 以截图为主，坐标点击为辅 |
| 加载时间 | 3-5秒或更长 |

## 有效模式

### 模式1：纯截图查看（最可靠）
```bash
browser.sh start "https://www.douyin.com"
sleep 5
element.py --screenshot /tmp/douyin.png
```

### 模式2：点击操作
```bash
# 先截图查看元素位置
element.py --screenshot /tmp/before.png

# 使用JavaScript点击（推荐）
element.py --click-text "登录" --js-click

# 点击后截图确认
element.py --screenshot /tmp/after.png
```

## 已知陷阱

### 陷阱1：元素查找失效
**现象：** `--find "登录"` 返回"未找到匹配元素"
**原因：** 抖音使用 Canvas 渲染，传统 DOM 元素很少
**解决：** 
1. 告知用户"元素查找失败，尝试使用JavaScript点击..."
2. 使用 `--js-click` 点击
3. 如果仍然失败，告知用户"JavaScript点击也失败了，尝试其他方法..."
4. 可以尝试其他方法（如截图+坐标点击）
5. 如果所有方法都失败，告知用户"操作失败，请稍后重试"

### 陷阱2：页面加载超时
**现象：** 截图显示空白或加载中
**原因：** 抖音资源较多，网络慢时加载时间长
**解决：** 增加等待时间到 5-10 秒

### 陷阱3：CDP 连接失败（已修复）
**现象：** `无法连接CDP` 或 `Handshake status 403`
**原因：** Chrome 新版本需要 `--user-data-dir` 和 `--remote-allow-origins`
**解决：** 已在 browser.sh 中添加这两个参数

### 陷阱4：CPU 占用过高
**现象：** Chrome 进程 CPU 占用 100%+
**原因：** 抖音页面复杂，渲染进程卡死
**解决：** 
```bash
pkill -9 chrome
pkill -9 Xvfb
```

## 调试技巧

**黄金法则：截图优先，查找为辅**

```bash
# 每次操作后必须截图
element.py --screenshot /tmp/step1.png  # 操作前
element.py --click 100 200              # 执行操作  
element.py --screenshot /tmp/step2.png  # 操作后
```

**使用 Xvfb 截图作为备用：**
```bash
# 如果 CDP 截图失败，使用 Xvfb 截取整个虚拟屏幕
DISPLAY=:99 import -window root /tmp/xvfb_douyin.png
```

## 常见问题

**Q: 页面显示"访问太频繁"？**
A: 抖音反爬检测，等待一段时间再试，或更换IP

**Q: 视频无法播放？**
A: 有头浏览器可能缺少解码器，这是正常的，截图查看静态内容即可

**Q: 登录后很快被踢出？**
A: 抖音检测自动化工具，建议减少操作频率，模拟真人操作间隔

**Q: 为什么找不到任何元素？**
A: 抖音使用 Canvas 渲染，这是预期行为。请使用截图方式查看页面

## 更新记录

- **2026-04-13** - 初始版本，添加实际使用经验和陷阱记录
