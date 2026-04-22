#!/bin/bash
# browser.sh - 有头浏览器启动/管理脚本 (V3简化版)

CDP_PORT=${CDP_PORT:-18800}
DISPLAY_NUM=${DISPLAY_NUM:-99}
SCREEN_WIDTH=${SCREEN_WIDTH:-1920}
SCREEN_HEIGHT=${SCREEN_HEIGHT:-1080}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLOCKER_JS="$SCRIPT_DIR/blocker.js"

# 自动检测 Chrome 路径
detect_chrome() {
    if [ -n "$CHROME_PATH" ]; then
        echo "$CHROME_PATH"
        return
    fi

    # 常见 Chrome 路径
    local chrome_paths=(
        "/home/sandbox/chrome-linux/chrome"
        "/usr/bin/google-chrome"
        "/usr/bin/google-chrome-stable"
        "/usr/bin/chromium"
        "/usr/bin/chromium-browser"
        "/opt/google/chrome/google-chrome"
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    )

    for path in "${chrome_paths[@]}"; do
        if [ -x "$path" ]; then
            echo "$path"
            return
        fi
    done

    # 尝试 which
    if command -v google-chrome &> /dev/null; then
        command -v google-chrome
        return
    elif command -v google-chrome-stable &> /dev/null; then
        command -v google-chrome-stable
        return
    elif command -v chromium &> /dev/null; then
        command -v chromium
        return
    elif command -v chromium-browser &> /dev/null; then
        command -v chromium-browser
        return
    fi

    echo "Error: Chrome not found. Please install Google Chrome or Chromium." >&2
    exit 1
}

start_browser() {
    local url="$1"
    
    # 检查是否已运行
    if pgrep -f "chrome.*remote-debugging-port=$CDP_PORT" > /dev/null; then
        echo "浏览器已在运行 (CDP端口: $CDP_PORT)"
        return 0
    fi
    
    # 启动 Xvfb
    if ! pgrep -f "Xvfb.*:$DISPLAY_NUM" > /dev/null; then
        echo "启动 Xvfb :$DISPLAY_NUM (${SCREEN_WIDTH}x${SCREEN_HEIGHT})..."
        Xvfb :$DISPLAY_NUM -screen 0 ${SCREEN_WIDTH}x${SCREEN_HEIGHT}x24 &
        sleep 2
    fi
    
    # 用户数据目录（使用固定路径，避免 $$ 导致的目录变化问题）
    USER_DATA_DIR="/tmp/chrome-headed-v3-data"
    mkdir -p "$USER_DATA_DIR"
    
    # 创建 Preferences 文件，禁用会话恢复和崩溃提示
    PREFS_DIR="$USER_DATA_DIR/Default"
    mkdir -p "$PREFS_DIR"
    cat > "$PREFS_DIR/Preferences" << 'PREFS_EOF'
{
    "profile": {
        "default_content_setting_values": {
            "protocol_handler": 2
        }
    },
    "session": {
        "restore_on_startup": 5,
        "startup_urls": ["about:blank"]
    },
    "browser": {
        "enabled_labs_experiments": [
            "disable-external-intent-requests@2"
        ]
    }
}
PREFS_EOF
    
    # 清除会话恢复信息，防止"Restore pages"提示和恢复之前的标签页
    rm -rf "$USER_DATA_DIR/Singleton*" 2>/dev/null || true
    rm -f "$USER_DATA_DIR/Last*" 2>/dev/null || true
    rm -f "$USER_DATA_DIR/*_startup_log*" 2>/dev/null || true
    rm -rf "$USER_DATA_DIR/Default/Sessions" 2>/dev/null || true
    rm -f "$USER_DATA_DIR/Default/Current*" 2>/dev/null || true
    rm -f "$USER_DATA_DIR/Default/Last*" 2>/dev/null || true
    
    # 构建 Chrome 启动参数
    local chrome_args=(
        --no-sandbox
        --disable-setuid-sandbox
        --disable-dev-shm-usage
        --disable-gpu
        --disable-web-security
        --disable-features=IsolateOrigins,site-per-process
        --remote-debugging-port=$CDP_PORT
        --window-size=$SCREEN_WIDTH,$SCREEN_HEIGHT
        --force-device-scale-factor=1
        --disable-blink-features=AutomationControlled
        --disable-popup-blocking
        --no-first-run
        --no-default-browser-check
        --user-data-dir="$USER_DATA_DIR"
        --remote-allow-origins='*'
        # 保持运行相关参数
        --disable-background-timer-throttling
        --disable-backgrounding-occluded-windows
        --disable-renderer-backgrounding
        --disable-background-networking
        --disable-breakpad
        --disable-client-side-phishing-detection
        --disable-component-update
        --disable-default-apps
        --disable-hang-monitor
        --disable-ipc-flooding-protection
        --disable-prompt-on-repost
        --disable-sync
        --force-color-profile=srgb
        --metrics-recording-only
        --safebrowsing-disable-auto-update
        --password-store=basic
        --use-mock-keychain
        --enable-automation
        # 禁用恢复页面提示
        --disable-session-crashed-bubble
        --disable-restore-session-state
    )
    
    # 如果提供了URL，添加协议拦截脚本
    if [ -n "$url" ]; then
        if [ -f "$BLOCKER_JS" ]; then
            chrome_args+=(--inject-js="$BLOCKER_JS")
        fi
        chrome_args+=("$url")
    fi
    
    # 检测 Chrome 路径
    local chrome_path
    chrome_path=$(detect_chrome)
    echo "使用 Chrome: $chrome_path"
    
    echo "启动 Chrome (CDP端口: $CDP_PORT)..."
    DISPLAY=:$DISPLAY_NUM "$chrome_path" "${chrome_args[@]}" &
    
    sleep 3
    
    # 验证启动
    if pgrep -f "chrome.*remote-debugging-port=$CDP_PORT" > /dev/null; then
        echo "浏览器启动成功"
        echo "CDP端口: $CDP_PORT"
        echo "显示: :$DISPLAY_NUM"
        [ -n "$url" ] && echo "打开URL: $url"
        return 0
    else
        echo "浏览器启动失败"
        return 1
    fi
}

stop_browser() {
    echo "停止浏览器..."
    pkill -f "chrome.*remote-debugging-port=$CDP_PORT" 2>/dev/null
    pkill -f "Xvfb.*:$DISPLAY_NUM" 2>/dev/null
    echo "已停止"
}

check_status() {
    if pgrep -f "chrome.*remote-debugging-port=$CDP_PORT" > /dev/null; then
        echo "浏览器运行中 (CDP端口: $CDP_PORT)"
        return 0
    else
        echo "浏览器未运行"
        return 1
    fi
}

case "${1:-}" in
    start)
        start_browser "${2:-}"
        ;;
    stop)
        stop_browser
        ;;
    status)
        check_status
        ;;
    *)
        echo "用法: $0 {start [URL]|stop|status}"
        echo ""
        echo "示例:"
        echo "  $0 start                    # 启动浏览器"
        echo "  $0 start https://example.com # 启动并打开网页"
        echo "  $0 status                   # 检查状态"
        echo "  $0 stop                     # 停止浏览器"
        exit 1
        ;;
esac
