# Headed Browser Open V3

在沙箱环境中使用有头浏览器(headed browser)进行网页自动化操作，通过 CDP (Chrome DevTools Protocol) 控制浏览器，支持元素查找、点击、输入、截图等功能。

## 核心特性

- **真实 Chrome 浏览器** - 非 headless 模式，更难被反爬虫检测
- **CDP 协议控制** - 支持元素查找、点击、输入、截图
- **协议拦截** - 自动拦截外部协议弹窗（weixin://, taobao:// 等）
- **Xvfb 虚拟显示** - 无需物理显示器即可运行

## 适用场景

| 场景 | 适用性 | 说明 |
|------|--------|------|
| 绕过反爬虫检测 | ✅ | 有头浏览器更接近真实用户 |
| 拦截 App 唤起弹窗 | ✅ | 自动拦截 weixin:// 等外部协议 |
| 小红书、抖音等平台 | ✅ | 已验证兼容 |
| 简单页面抓取 | ❌ | 建议使用无头浏览器 |

## 前置要求

```bash
# Ubuntu/Debian
apt-get update
apt-get install -y xvfb google-chrome-stable python3-pip
pip3 install websocket-client
```

## 快速开始

### 1. 启动浏览器

```bash
./scripts/browser.sh start "https://www.xiaohongshu.com" &
sleep 3
```

### 2. 截图确认

```bash
./scripts/element.py --screenshot /tmp/page.png
```

### 3. 查找并点击元素

```bash
# 查找元素
./scripts/element.py --find "登录,手机号"

# 点击元素（使用 JavaScript 点击绕过反爬）
./scripts/element.py --click-text "获取验证码" --js-click
```

### 4. 输入文本

```bash
# 点击输入框获取焦点
./scripts/element.py --click 960 438

# 输入文本
./scripts/element.py --type "13800138000"
```

## 脚本说明

### browser.sh - 浏览器管理

| 命令 | 说明 | 示例 |
|------|------|------|
| `start [URL]` | 启动浏览器 | `browser.sh start "https://example.com"` |
| `status` | 检查状态 | `browser.sh status` |
| `stop` | 停止浏览器 | `browser.sh stop` |

### element.py - 元素操作

| 参数 | 说明 | 示例 |
|------|------|------|
| `--find TEXT` | 查找元素 | `--find "登录,手机号"` |
| `--click X Y` | 坐标点击 | `--click 1077 586` |
| `--click-text TEXT` | 文本点击 | `--click-text "登录" --js-click` |
| `--type TEXT` | 输入文本 | `--type "13800138000"` |
| `--screenshot PATH` | 截图 | `--screenshot /tmp/page.png` |

### element_iframe.py - iframe 处理

| 参数 | 说明 | 示例 |
|------|------|------|
| `--list-frames` | 列出所有 frames | `--list-frames` |
| `--iframe PATTERN` | 指定 iframe | `--iframe "x-URS"` |
| `--click-text TEXT` | 点击 iframe 内元素 | `--click-text "登录"` |

## 场景文件

`scenarios/` 目录包含各网站的特定操作指南：

| 文件 | 网站 | 说明 |
|------|------|------|
| `xiaohongshu.com.md` | 小红书 | DOM+Canvas混合 |
| `douyin.com.md` | 抖音 | 纯Canvas渲染 |
| `zhihu.com.md` | 知乎 | 标准DOM渲染 |
| `bilibili.com.md` | B站 | 建议使用JS点击 |
| `generic.md` | 通用 | 通用原则和最佳实践 |

## 重要提示

### 手机号登录流程

**必须先勾选"我已阅读并同意"，再点击"获取验证码"！**

1. 输入手机号
2. **勾选同意协议** ⚠️
3. 点击获取验证码

### 坐标参考（1920x1080）

| 网站 | 元素 | 坐标 |
|------|------|------|
| 小红书 | 同意协议复选框 | (1077, 586) |
| 小红书 | 获取验证码按钮 | (1256, 438) |

### 强制截图

每次操作后必须截图确认：

```bash
./scripts/element.py --screenshot /tmp/after_action.png
```

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| 浏览器启动失败 | `apt-get install xvfb google-chrome-stable` |
| CDP 连接失败 | 检查 `browser.sh status`，更换端口 |
| 元素找不到 | 增加 `sleep` 等待时间 |
| 点击无反应 | 使用 `--js-click` 参数 |
| Chrome CPU 占用高 | `pkill -9 chrome` 强制终止 |

## 技术原理

### 协议拦截

通过 Chrome 启动参数注入 `blocker.js`，劫持 `window.location` 和 `window.open()`，阻止非 HTTP 协议跳转。

### CDP 连接

```
element.py → WebSocket → Chrome CDP (port 18800)
                ↓
         执行浏览器操作
```

### 截图机制

1. 尝试 CDP 截图 (`Page.captureScreenshot`)
2. 失败则回退到 Xvfb 截图 (`import -window root`)

## 文件结构

```
.
├── README.md              # 本文件
├── SKILL.md               # 详细技能文档
├── scripts/
│   ├── browser.sh         # 浏览器启动脚本
│   ├── element.py         # 元素操作脚本
│   ├── element_iframe.py  # iframe 处理脚本
│   ├── blocker.js         # 协议拦截脚本
│   └── playwright_iframe_demo.py  # Playwright 示例
└── scenarios/             # 网站特定场景
    ├── xiaohongshu.com.md
    ├── douyin.com.md
    ├── zhihu.com.md
    ├── bilibili.com.md
    └── generic.md
```

## License

MIT
