# Headed Browser Open V3

给 OpenClaw 补上**云侧有头浏览器能力**，让 Agent 能操控真实 Chrome 完成复杂网页自动化。

[⚡ 快速开始](#快速开始) · [📖 设计原理](#设计原理) · [🎯 场景示例](#场景示例)

---

OpenClaw 原生的 `browser` skill 是无头浏览器，面对现代网站的反爬检测、App 唤起弹窗、Canvas 渲染等场景力不从心。这个 Skill 补上的是：**真实 Chrome 环境 + 反爬绕过 + 经验积累机制**。

## 能力矩阵

| 能力 | 说明 |
|------|------|
| **云侧有头浏览器** | 真实 Chrome（非 headless），运行在 Xvfb 虚拟显示中，无需物理显示器 |
| **反爬绕过** | 自动拦截外部协议弹窗（weixin://, taobao://），支持 JS 点击绕过检测 |
| **经验机制，越用越聪明** | 按域名存储操作经验（平台特征、已知陷阱、有效模式），跨 session 复用 |
| **小红书/抖音登录** | 已验证支持小红书、抖音、知乎、B站等国内平台的登录流程 |
| **CDP 协议控制** | 元素查找、点击、输入、截图，支持 iframe 穿透 |
| **三重截图保障** | CDP 截图 → Xvfb 截图 → 错误回退，确保每次操作可追溯 |

---

## 快速开始

### 安装依赖

```bash
# Ubuntu/Debian
apt-get update
apt-get install -y xvfb google-chrome-stable python3-pip
pip3 install websocket-client
```

### 1. 启动浏览器访问小红书

```bash
./scripts/browser.sh start "https://www.xiaohongshu.com" &
sleep 3
```

### 2. 截图确认页面状态

```bash
./scripts/element.py --screenshot /tmp/xhs_home.png
```

### 3. 登录流程（手机号+验证码）

```bash
# 查找登录相关元素
./scripts/element.py --find "登录,手机号,同意"

# 点击"同意协议"复选框（必须先勾选！）
./scripts/element.py --click 1077 586

# 点击手机号输入框并输入
./scripts/element.py --click 960 438
./scripts/element.py --type "13800138000"

# 点击获取验证码（使用 JS 点击绕过反爬）
./scripts/element.py --click-text "获取验证码" --js-click
```

### 4. 每次操作后截图验证

```bash
./scripts/element.py --screenshot /tmp/after_login.png
```

---

## 设计原理

### 为什么需要云侧有头浏览器？

| 场景 | 无头浏览器 | 有头浏览器（本 Skill） |
|------|-----------|----------------------|
| 反爬检测 | ❌ 容易被识别 | ✅ 真实 Chrome 环境 |
| App 唤起弹窗 | ❌ 无法处理 | ✅ 自动拦截 weixin:// 等协议 |
| Canvas 渲染页面（抖音） | ❌ 难以操作 | ✅ 支持截图+坐标点击 |
| 需要登录态 | ❌ 每次重新登录 | ✅ 可保持会话 |

### 协议拦截机制

页面加载前注入 `blocker.js`，劫持非 HTTP 协议跳转：

```javascript
// 拦截 weixin://, taobao:// 等外部协议
Object.defineProperty(window, 'location', {
    set: function(url) {
        if (url && !url.match(/^https?:\/\//i)) {
            console.log('[Blocker] Blocked:', url);
            return; // 阻止跳转
        }
        window.location.href = url;
    }
});
```

### 经验机制：越用越聪明

**问题**：每个网站有独特的反爬策略、元素结构、登录流程，重复踩坑浪费时间。

**解决**：按域名存储操作经验，跨 session 复用。

```
访问 https://www.xiaohongshu.com
        ↓
读取 scenarios/xiaohongshu.com.md
        ↓
获取已知信息：
  - 平台特征：DOM+Canvas 混合渲染
  - 登录陷阱：必须先勾选"同意协议"才能获取验证码
  - 有效模式：使用 --js-click 绕过点击检测
  - 坐标参考：1920x1080 下同意框坐标 (1077, 586)
        ↓
按经验执行 → 成功
        ↓
发现新问题 → 更新场景文件 → 下次复用
```

**场景文件索引**：

| 网站 | 经验文件 | 核心经验 |
|------|---------|---------|
| 小红书 | `scenarios/xiaohongshu.com.md` | 先勾选同意协议，JS 点击绕过检测 |
| 抖音 | `scenarios/douyin.com.md` | 纯 Canvas 渲染，截图+坐标为主 |
| 知乎 | `scenarios/zhihu.com.md` | 标准 DOM，支持动态查找 |
| B站 | `scenarios/bilibili.com.md` | 建议使用 JS 点击 |

---

## 场景示例

### 场景 1：小红书关键词搜索

```bash
# 1. 启动并访问搜索页
./scripts/browser.sh start "https://www.xiaohongshu.com/search_result?keyword=AI" &
sleep 3

# 2. 截图确认加载完成
./scripts/element.py --screenshot /tmp/xhs_search.png

# 3. 滚动加载更多（如需）
./scripts/element.py --click 960 600  # 点击页面中央
sleep 1
./scripts/element.py --screenshot /tmp/xhs_scroll.png
```

### 场景 2：抖音视频分析

```bash
# 1. 启动访问抖音
./scripts/browser.sh start "https://www.douyin.com" &
sleep 5

# 2. 截图（抖音是 Canvas 渲染，用截图分析）
./scripts/element.py --screenshot /tmp/douyin.png

# 3. 根据截图坐标点击视频
./scripts/element.py --click 500 400
sleep 2
./scripts/element.py --screenshot /tmp/douyin_video.png
```

### 场景 3：iframe 内登录（163邮箱示例）

```bash
# 1. 列出所有 iframe
./scripts/element_iframe.py --list-frames

# 2. 在登录 iframe 内操作
./scripts/element_iframe.py --iframe "x-URS" --type "your_email@163.com"
./scripts/element_iframe.py --iframe "x-URS" --click-text "登录"
```

---

## 工具脚本

### browser.sh - 浏览器生命周期

```bash
./scripts/browser.sh start [URL]   # 启动浏览器，可选打开 URL
./scripts/browser.sh status        # 检查运行状态
./scripts/browser.sh stop          # 停止浏览器
```

**环境变量**：
- `CDP_PORT=18800` - CDP 调试端口
- `DISPLAY_NUM=99` - Xvfb 显示号
- `SCREEN_WIDTH=1920` / `SCREEN_HEIGHT=1080` - 屏幕分辨率

### element.py - 元素操作核心

| 参数 | 功能 | 反爬场景建议 |
|------|------|-------------|
| `--find TEXT` | 查找包含文本的元素 | 先 find 定位，再操作 |
| `--click X Y` | 坐标点击 | Canvas 页面必备 |
| `--click-text TEXT` | 文本匹配点击 | 标准 DOM 页面 |
| `--js-click` | JavaScript 点击 | **绕过反爬检测首选** |
| `--type TEXT` | 输入文本 | 先点击输入框获取焦点 |
| `--screenshot PATH` | 截图保存 | **每次操作后必做** |

### element_iframe.py - iframe 穿透

| 参数 | 功能 |
|------|------|
| `--list-frames` | 列出页面所有 iframe |
| `--iframe PATTERN` | 进入指定 iframe（URL/name 匹配） |
| `--click-text TEXT` | 在 iframe 内点击 |
| `--type TEXT` | 在 iframe 内输入 |

---

## 经验积累实战

### 发现新问题 → 记录经验

**场景**：操作小红书时发现"获取验证码"按钮点击无响应。

**排查**：
1. 截图确认页面状态
2. 发现未勾选"同意协议"复选框
3. 勾选后按钮可点击

**记录到 `scenarios/xiaohongshu.com.md`**：

```markdown
## 已知陷阱

### 陷阱 1：必须先勾选同意协议
- **现象**：点击"获取验证码"无响应
- **原因**：未勾选"我已阅读并同意"复选框
- **解决**：先点击复选框 (1920x1080 坐标: 1077, 586)，再获取验证码
```

**下次访问**：自动读取经验，避免重复踩坑。

---

## 故障排查

| 问题 | 原因 | 解决 |
|------|------|------|
| 浏览器启动失败 | Xvfb 未安装 | `apt-get install xvfb` |
| CDP 连接失败 | 端口冲突 | 更换 `CDP_PORT` 环境变量 |
| 元素找不到 | 页面未加载完 | 增加 `sleep` 等待时间 |
| 点击无反应 | 被反爬检测 | 添加 `--js-click` 参数 |
| 验证码按钮无响应 | 未勾选同意协议 | 先勾选复选框（见小红书经验） |
| Chrome CPU 占用高 | 页面卡死 | `pkill -9 chrome` 强制终止 |

---

## 与 OpenClaw 原生能力对比

| 能力 | OpenClaw `browser` | 本 Skill |
|------|-------------------|---------|
| 浏览器类型 | Headless（无头） | Headed（有头） |
| 反爬检测 | 容易被识别 | 真实环境，更难检测 |
| App 唤起弹窗 | 无法处理 | 自动拦截 |
| 运行环境 | 本地/云端均可 | 需 Xvfb（云端适用） |
| 登录态保持 | 困难 | 支持 |
| 经验积累 | 无 | 按域名存储，越用越聪明 |

---

## 文件结构

```
headed-browser-open-v3/
├── README.md              # 本文件
├── SKILL.md               # 详细使用文档（Agent 读取）
├── scripts/
│   ├── browser.sh         # 浏览器启动/停止
│   ├── element.py         # 元素操作核心
│   ├── element_iframe.py  # iframe 处理
│   ├── blocker.js         # 协议拦截脚本
│   └── playwright_iframe_demo.py  # Playwright 示例
└── scenarios/             # 🧠 经验积累目录
    ├── xiaohongshu.com.md # 小红书经验
    ├── douyin.com.md      # 抖音经验
    ├── zhihu.com.md       # 知乎经验
    ├── bilibili.com.md    # B站经验
    └── generic.md         # 通用经验
```

---

## License

MIT
# 伊丽莎白测试提交
