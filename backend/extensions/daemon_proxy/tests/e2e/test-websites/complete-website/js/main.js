// 完整网站 JavaScript 功能

document.addEventListener('DOMContentLoaded', function() {
    // 初始化统计数字动画
    initStatsAnimation();
    
    // 初始化导航栏滚动效果
    initNavbarScroll();
    
    // 初始化特性卡片动画
    initFeatureAnimations();
    
    // 模拟统计数据
    simulateStats();
    
    console.log('🌐 完整网站加载完成！');
});

// 统计数字动画
function initStatsAnimation() {
    const statNumbers = document.querySelectorAll('.stat-number');
    
    const animateNumber = (element, target) => {
        let current = 0;
        const increment = target / 100;
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            element.textContent = Math.floor(current);
        }, 20);
    };
    
    // 使用 Intersection Observer 来触发动画
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                const target = parseInt(element.dataset.target || '1000');
                animateNumber(element, target);
                observer.unobserve(element);
            }
        });
    });
    
    statNumbers.forEach(stat => {
        observer.observe(stat);
    });
}

// 导航栏滚动效果
function initNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    let lastScrollY = window.scrollY;
    
    window.addEventListener('scroll', () => {
        const currentScrollY = window.scrollY;
        
        if (currentScrollY > 100) {
            navbar.style.background = 'rgba(255, 255, 255, 0.95)';
            navbar.style.backdropFilter = 'blur(10px)';
        } else {
            navbar.style.background = '#fff';
            navbar.style.backdropFilter = 'none';
        }
        
        lastScrollY = currentScrollY;
    });
}

// 特性卡片动画
function initFeatureAnimations() {
    const featureItems = document.querySelectorAll('.feature-item');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, {
        threshold: 0.1
    });
    
    featureItems.forEach((item, index) => {
        item.style.opacity = '0';
        item.style.transform = 'translateY(30px)';
        item.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
        observer.observe(item);
    });
}

// 模拟统计数据
function simulateStats() {
    // 设置目标数据
    document.getElementById('total-requests').dataset.target = '12547';
    document.getElementById('active-links').dataset.target = '89';
    document.getElementById('uptime').dataset.target = '168';
    
    // 模拟实时更新
    setInterval(() => {
        const totalRequests = document.getElementById('total-requests');
        const activeLinks = document.getElementById('active-links');
        const uptime = document.getElementById('uptime');
        
        // 随机增加请求数
        const currentRequests = parseInt(totalRequests.textContent);
        if (currentRequests > 0) {
            totalRequests.textContent = currentRequests + Math.floor(Math.random() * 3);
        }
        
        // 随机变化活跃链接数
        const currentLinks = parseInt(activeLinks.textContent);
        if (currentLinks > 0) {
            const change = Math.floor(Math.random() * 3) - 1; // -1, 0, 1
            activeLinks.textContent = Math.max(0, currentLinks + change);
        }
    }, 5000);
}

// 页面性能监控
function logPerformanceMetrics() {
    if (window.performance && window.performance.timing) {
        const timing = window.performance.timing;
        const loadTime = timing.loadEventEnd - timing.navigationStart;
        const domReady = timing.domContentLoadedEventEnd - timing.navigationStart;
        
        console.log('📊 页面性能指标：');
        console.log('- 总加载时间:', loadTime + 'ms');
        console.log('- DOM 准备时间:', domReady + 'ms');
        console.log('- 首次绘制时间:', timing.responseStart - timing.navigationStart + 'ms');
    }
}

// 页面加载完成后记录性能指标
window.addEventListener('load', logPerformanceMetrics);

// 错误处理
window.addEventListener('error', function(e) {
    console.error('❌ 页面错误:', e.error);
});

// 资源加载错误处理
window.addEventListener('unhandledrejection', function(e) {
    console.error('❌ 未处理的 Promise 拒绝:', e.reason);
});
