// blocker.js - 协议拦截脚本 (V3)
// 在页面加载前注入，阻止外部协议弹窗

(function() {
    'use strict';
    
    const BLOCKED_PROTOCOLS = /^(weixin|wechat|alipay|taobao|openapp|dianping|meituan|jd|tmall):\/\//i;
    
    // 劫持 window.location
    const originalLocation = window.location;
    Object.defineProperty(window, 'location', {
        get: function() {
            return originalLocation;
        },
        set: function(url) {
            if (url && BLOCKED_PROTOCOLS.test(url)) {
                console.log('[Blocker] Blocked protocol:', url);
                return;
            }
            originalLocation.href = url;
        },
        configurable: false
    });
    
    // 劫持 window.open
    const originalOpen = window.open;
    window.open = function(url, target, features) {
        if (url && BLOCKED_PROTOCOLS.test(url)) {
            console.log('[Blocker] Blocked window.open:', url);
            return null;
        }
        return originalOpen.apply(this, arguments);
    };
    
    // 劫持 a 标签点击
    document.addEventListener('click', function(e) {
        const el = e.target.closest('a');
        if (el && el.href && BLOCKED_PROTOCOLS.test(el.href)) {
            console.log('[Blocker] Blocked link:', el.href);
            e.preventDefault();
            e.stopPropagation();
        }
    }, true);
    
    console.log('[Blocker] Protocol blocker initialized');
})();
