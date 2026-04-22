---
domain: zhihu.com
aliases: [知乎, zhihu]
updated: 2026-04-14
---

# 知乎自动化场景

## 场景说明

知乎（zhihu.com）是一个问答社区平台，使用 headed-browser-open-v3 可以打开知乎网页并进行自动化操作。

## 快速开始

```bash
# 1. 启动浏览器并打开知乎
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/browser.sh start "https://www.zhihu.com"
sleep 4

# 2. 截图确认页面状态
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --screenshot /tmp/zhihu_home.png
```

## 平台特征

| 特征 | 说明 |
|------|------|
| 渲染方式 | DOM + 部分动态加载 |
| 登录方式 | 手机号/邮箱/第三方账号 |
| 反爬策略 | 中等，有基本的风控检测 |
| 协议弹窗 | 较少，但可能有 App 推广 |

## 有效模式

### 模式1：打开首页并截图
```bash
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/browser.sh start "https://www.zhihu.com"
sleep 4
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --screenshot /tmp/zhihu.png
```

### 模式2：打开特定问题页面
```bash
QUESTION_URL="https://www.zhihu.com/question/XXXXXX"
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/browser.sh start "$QUESTION_URL"
sleep 4
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/element.py --screenshot /tmp/zhihu_question.png
```

### 模式3：搜索话题
```bash
# 打开知乎搜索页
~/.openclaw/workspace/skills/headed-browser-open-v3/scripts/browser.sh start "https://www.zhihu.com/search"
sleep 4

# 截图查看搜索框位置
element.py --screenshot /tmp/zhihu_search.png

# 使用JavaScript点击搜索框
element.py --click-text "搜索" --js-click

# 输入搜索词
element.py --type "搜索关键词"
```

## 已知陷阱

### 陷阱1：登录弹窗
**现象：** 未登录状态下浏览一定数量内容后会弹出登录提示
**解决：** 目前仅支持浏览公开内容，登录功能需进一步验证

### 陷阱2：点击失败
**现象：** 点击元素没有反应
**原因：** 知乎有反自动化检测
**解决：** 
1. 告知用户"点击失败，尝试使用JavaScript点击..."
2. 使用 `--js-click` 参数重试
3. 如果仍然失败，告知用户"JavaScript点击也失败了，尝试其他方法..."
4. 可以尝试其他方法（如动态查找元素位置后点击）
5. 如果所有方法都失败，告知用户"操作失败，请稍后重试"

### 陷阱3：无限滚动
**现象：** 知乎首页和问题页面使用无限滚动加载
**解决：** 如需加载更多内容，可模拟滚动操作（需通过 CDP 执行 JavaScript）

## 常见问题

**Q: 知乎需要登录才能查看吗？**
A: 部分公开内容可以匿名查看，但大量浏览后会触发登录提示。

**Q: 如何绕过登录？**
A: 目前脚本仅支持浏览公开内容，登录功能需要进一步开发和测试。

## 更新记录

- **2026-04-14** - 初始场景创建
