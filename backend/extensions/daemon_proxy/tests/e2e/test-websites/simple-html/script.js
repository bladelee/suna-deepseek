// 简单静态网站 JavaScript 功能测试

document.addEventListener('DOMContentLoaded', function() {
    // 显示当前时间
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
    
    // 显示用户代理信息
    document.getElementById('user-agent').textContent = navigator.userAgent;
    
    // 显示页面URL
    document.getElementById('page-url').textContent = window.location.href;
    
    // 绑定测试按钮事件
    const testButton = document.getElementById('test-button');
    const testResult = document.getElementById('test-result');
    
    testButton.addEventListener('click', function() {
        // 模拟一些交互功能
        testResult.textContent = '✅ JavaScript 功能正常工作！时间：' + new Date().toLocaleString();
        testResult.classList.add('show');
        
        // 添加一些视觉效果
        testButton.style.background = '#27ae60';
        testButton.textContent = '✅ 测试成功！';
        
        setTimeout(() => {
            testButton.style.background = '#3498db';
            testButton.textContent = '点击测试 JavaScript';
        }, 2000);
    });
    
    // 添加页面加载完成的提示
    console.log('🚀 静态网站加载完成！');
    console.log('📊 页面信息：');
    console.log('- URL:', window.location.href);
    console.log('- 用户代理:', navigator.userAgent);
    console.log('- 屏幕尺寸:', window.screen.width + 'x' + window.screen.height);
    console.log('- 视口尺寸:', window.innerWidth + 'x' + window.innerHeight);
});

function updateCurrentTime() {
    const now = new Date();
    const timeString = now.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    document.getElementById('current-time').textContent = timeString;
}

// 添加一些额外的测试功能
function testLocalStorage() {
    try {
        localStorage.setItem('daemon-proxy-test', 'success');
        const value = localStorage.getItem('daemon-proxy-test');
        return value === 'success';
    } catch (e) {
        return false;
    }
}

function testSessionStorage() {
    try {
        sessionStorage.setItem('daemon-proxy-test', 'success');
        const value = sessionStorage.getItem('daemon-proxy-test');
        return value === 'success';
    } catch (e) {
        return false;
    }
}

// 页面加载完成后运行存储测试
window.addEventListener('load', function() {
    console.log('💾 本地存储测试:', testLocalStorage() ? '✅ 通过' : '❌ 失败');
    console.log('💾 会话存储测试:', testSessionStorage() ? '✅ 通过' : '❌ 失败');
});
