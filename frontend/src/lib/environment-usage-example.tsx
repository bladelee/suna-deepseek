import React from 'react';
import { isElectron, isWeb } from './config';

/**
 * 环境检测函数使用示例
 * 
 * 这些函数可用于在组件中条件渲染不同的内容，具体取决于应用是在Electron客户端还是Web客户端中运行。
 * 
 * 使用场景：
 * 1. 当某个功能只在特定环境中可用时
 * 2. 当界面元素在不同环境中需要有不同表现时
 * 3. 当需要调用特定环境API时（如Electron的原生对话框）
 */

export const EnvironmentSpecificComponent = () => {
  if (isElectron()) {
    // 在Electron环境中显示的内容
    return (
      <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <h3 className="font-semibold text-blue-700 dark:text-blue-300">Electron环境</h3>
        <p className="text-sm text-blue-600 dark:text-blue-400">
          这是在桌面应用中显示的特定内容
        </p>
        <button 
          className="mt-2 px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
          onClick={() => {
            // 调用Electron特定API示例
            if (typeof window !== 'undefined' && window.electronAPI) {
              window.electronAPI.showMessage('这是一个Electron对话框消息');
            }
          }}
        >
          显示Electron对话框
        </button>
      </div>
    );
  }
  
  // 在Web环境中显示的内容
  return (
    <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
      <h3 className="font-semibold text-green-700 dark:text-green-300">Web环境</h3>
      <p className="text-sm text-green-600 dark:text-green-400">
        这是在Web浏览器中显示的特定内容
      </p>
      <a 
        href="#web-specific-feature" 
        className="mt-2 inline-block px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
      >
        访问Web特定功能
      </a>
    </div>
  );
};

/**
 * 在业务逻辑中使用环境检测
 */
export const performEnvironmentSpecificAction = () => {
  if (isElectron()) {
    console.log('执行Electron特定操作');
    // 调用Electron特定API
  } else if (isWeb()) {
    console.log('执行Web特定操作');
    // 调用Web特定API
  }
};

/**
 * 获取环境特定的配置
 */
export const getEnvironmentConfig = () => {
  if (isElectron()) {
    return {
      storageType: 'local-file',
      securityLevel: 'desktop',
      // 其他Electron特定配置
    };
  }
  
  return {
    storageType: 'cloud',
    securityLevel: 'web',
    // 其他Web特定配置
  };
};