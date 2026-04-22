---
domain: xiaohongshu.com
aliases: [小红书, 小红薯, XHS]
updated: 2026-04-13
---

# 小红书自动化场景

## 快速开始（推荐）

```bash
# 1. 启动浏览器打开小红书
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/browser.sh start "https://www.xiaohongshu.com"

# 2. 等待页面加载
sleep 3

# 3. 截图查看当前状态
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --screenshot /tmp/xhs_status.png
```

## 单标签页模式（浏览内容）

适用于：查看页面、简单点击、不需要登录的场景

```bash
# 启动并截图
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/browser.sh start "https://www.xiaohongshu.com"
sleep 3
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --screenshot /tmp/xhs_browse.png
```

## 双标签页模式（登录操作）

适用于：需要登录、获取验证码等复杂操作

```bash
# === 标签页1: 操作页面 ===

# 1. 启动浏览器打开小红书
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/browser.sh start "https://www.xiaohongshu.com"
sleep 3

# 2. 查找登录相关元素
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --find "登录,手机号,同意"

# 3. 点击"同意协议"复选框（必须先勾选！）
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --click 1077 586

# 4. 输入手机号
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --type "13800138000"

# 5. 点击获取验证码
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --click-text "获取验证码"

# 6. 截图确认
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --screenshot /tmp/xhs_step1.png

# === 标签页2: 等待验证码 ===
# 此时需要用户在手机上查看验证码，然后回来输入

# 7. 输入验证码（用户告知后）
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --type "123456"

# 8. 点击登录
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --click-text "登录"

# 9. 最终截图
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --screenshot /tmp/xhs_logged_in.png
```

## 平台特征

| 特征 | 说明 |
|------|------|
| 渲染方式 | 混合使用 DOM + Canvas |
| 反爬强度 | 中等 |
| 元素查找 | `--find` 可以找到部分元素 |
| 协议弹窗 | 会触发 weixin:// 等外部协议 |
| 推荐策略 | 元素查找 + 坐标点击结合 |

## 有效模式

### 模式1：元素查找优先
```bash
# 小红书支持元素文本查找
element.py --find "登录,手机号"
element.py --click-text "获取验证码"
```

### 模式2：坐标点击（精确控制）
```bash
# 关键坐标（1920x1080分辨率）
element.py --click 1077 586  # 同意协议复选框
element.py --click 1256 438  # 获取验证码按钮
```

**关键坐标表（1920x1080分辨率）：**

| 元素 | X | Y | 说明 |
|------|---|---|------|
| 同意协议复选框 | 1077 | 586 | ⚠️ 必须先勾选 |
| 手机号输入框 | 960 | 438 | 居中位置 |
| 获取验证码按钮 | 1256 | 438 | 勾选后才可点击 |
| 验证码输入框 | 960 | 520 | 短信验证码 |
| 登录按钮 | 960 | 600 | 最后点击 |

## 已知陷阱

### 陷阱1：未勾选协议就点击获取验证码
**现象：** 点击"获取验证码"没有任何反应
**原因：** 小红书在用户协议未勾选时禁用验证码按钮
**解决：** 
1. 先点击同意协议复选框
2. 如果点击失败，回复用户"操作失败，请稍后重试"

### 陷阱2：点击失败
**现象：** 点击元素没有反应
**原因：** 小红书有反自动化检测，或元素位置变化
**解决：** 
1. 告知用户"点击失败，尝试使用JavaScript点击..."
2. 使用 `--js-click` 参数重试
3. 如果仍然失败，告知用户"JavaScript点击也失败了，尝试其他方法..."
4. 可以尝试其他方法（如动态查找元素位置后点击）
5. 如果所有方法都失败，告知用户"操作失败，请稍后重试"

### 陷阱3：协议弹窗干扰
**现象：** 页面跳转时弹出"是否打开微信"等提示
**原因：** 小红书尝试唤起 App
**解决：** browser.sh 已自动注入 blocker.js 拦截协议弹窗

### 陷阱4：CDP 连接失败（已修复）
**现象：** `无法连接CDP` 或 `Handshake status 403`
**解决：** 已在 browser.sh 中添加 `--user-data-dir` 和 `--remote-allow-origins`

## 重要提示

### 手机号登录流程（必须遵守）

**正确顺序：**
1. 输入手机号
2. **勾选同意协议** ⚠️
3. 点击获取验证码

**错误顺序：**
1. 输入手机号
2. 点击获取验证码 ❌（按钮无响应）

## 调试技巧

**每次操作后截图确认：**
```bash
element.py --screenshot /tmp/before.png  # 操作前
element.py --click 1077 586               # 执行操作
element.py --screenshot /tmp/after.png   # 操作后
```

**验证元素查找结果：**
```bash
# 查找会返回元素位置和文本
element.py --find "登录,手机号"
# 输出示例：
# 找到 3 个匹配元素:
#   [1] DIV: '登录' at (960, 300)
#   [2] SPAN: '手机号登录' at (960, 400)
```

## 常见问题

**Q: 点击获取验证码没反应？**
A: 检查是否已勾选"我已阅读并同意"复选框

**Q: 坐标不准确？**
A: 不同分辨率下坐标会变化，使用 `--find` 查看元素位置，或按比例调整

**Q: 页面加载慢？**
A: 增加 `sleep` 等待时间到 5 秒，或先截图查看加载状态

**Q: 为什么弹出"打开微信"提示？**
A: 协议拦截脚本应该已阻止，如仍出现请检查 blocker.js 是否注入成功

## 更新记录

- **2026-04-13** - 添加平台特征、有效模式、已知陷阱等结构化经验
