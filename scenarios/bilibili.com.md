---
domain: bilibili.com
aliases: [B站, 哔哩哔哩, bilibili]
updated: 2026-04-14
---

# B站自动化场景

## 快速开始

```bash
# 1. 启动浏览器打开B站
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/browser.sh start "https://www.bilibili.com"
sleep 5

# 2. 截图查看当前状态
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --screenshot /tmp/bilibili_status.png
```

## 平台特征

| 特征 | 说明 |
|------|------|
| 渲染方式 | 标准DOM + 部分动态加载 |
| 反爬强度 | 中等 |
| 元素查找 | `--find` 可以找到部分元素 |
| 登录方式 | 支持密码、短信、二维码 |
| 协议弹窗 | 较少 |

## 有效模式

### 模式1：点击登录按钮

B站登录按钮在页面右上角，使用 `--js-click` 更可靠：

```bash
# 使用JavaScript点击（推荐）
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --click-text "登录" --js-click
```

**注意：** B站登录按钮使用 `--click-text` 可能位置不准确，建议使用 `--js-click`。

### 模式2：搜索视频

```bash
# 1. 点击搜索框
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --click-text "搜索" --js-click

# 2. 输入搜索词
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --type "OpenClaw"

# 3. 截图查看结果
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --screenshot /tmp/bilibili_search.png
```

## 已知陷阱

### 陷阱1：点击登录无反应
**现象：** 使用 `--click-text "登录"` 点击后没有弹出登录框
**原因：** B站登录按钮位置计算不准确，或反爬检测拦截了CDP鼠标事件
**解决：** 
1. 告知用户"点击失败，尝试使用JavaScript点击..."
2. 使用 `--js-click` 参数重试：`element.py --click-text "登录" --js-click`
3. 如果仍然失败，告知用户"JavaScript点击也失败了，尝试其他方法..."
4. 可以尝试其他方法（如动态查找元素位置后点击）
5. 如果所有方法都失败，告知用户"操作失败，请稍后重试"

### 陷阱2：元素查找返回大量结果
**现象：** `--find "登录"` 返回十几个匹配元素
**原因：** B站页面结构复杂，多处包含"登录"文本
**解决：** 使用更精确的关键词，或直接使用 `--js-click` 点击第一个匹配项

## 登录流程

B站支持多种登录方式：

### 密码登录
```bash
# 1. 点击登录按钮
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --click-text "登录" --js-click
sleep 2

# 2. 截图查看登录框类型
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --screenshot /tmp/bilibili_login.png

# 3. 根据登录框类型继续操作（可能需要切换到密码登录标签）
# ...
```

### 二维码登录
B站默认显示二维码登录，需要用户手机扫码，自动化难度较高。

## 更新记录

- **2026-04-14** - 初始版本，记录B站点击登录的经验
