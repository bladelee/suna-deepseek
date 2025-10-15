# Kortix 应用中文国际化技术方案设计文档

## 1. 项目概述

### 1.1 项目背景
Kortix（原Suna）是一个开源的AI代理管理平台，包含Web端和Electron桌面端应用。当前应用完全基于英文，需要增加中文支持以提升用户体验。

### 1.2 技术栈
- **前端框架**: Next.js 15.3.1 + React 18
- **桌面应用**: Electron
- **开发语言**: TypeScript
- **UI框架**: Tailwind CSS + Radix UI
- **状态管理**: Zustand + React Query

### 1.3 架构特点
- **双入口架构**: `app/` (Next.js Web端) + `client/` (Electron端)
- **代码共享**: components/, lib/, hooks/, providers/ 等目录完全共享
- **独立运行**: Web和Electron可独立部署和使用

## 2. 国际化需求分析

### 2.1 现状分析
- **无i18n基础设施**: 所有文本硬编码在组件中
- **语言固定**: HTML lang="en"，无语言切换功能
- **影响范围**: 约330个文件包含硬编码字符串
- **特殊需求**: Electron菜单、系统对话框等原生元素需要翻译

### 2.2 支持语言
- **主要语言**: 简体中文 (zh-CN)
- **基础语言**: 英文 (en)
- **未来扩展**: 繁体中文 (zh-TW)、日文 (ja) 等

### 2.3 翻译范围
- **用户界面**: 按钮、标签、导航、表单等
- **内容文本**: 提示信息、帮助文档、错误消息等
- **Electron原生**: 菜单、对话框、系统提示等

## 3. 技术方案设计

### 3.1 方案选择：基于React Context的统一i18n系统

#### 选择理由
1. **代码共享友好**: 不受Next.js路由限制，可在app和client中同时使用
2. **Electron兼容**: 不依赖服务端渲染，适合Electron环境
3. **灵活性高**: 可以处理Electron特有的翻译需求
4. **统一管理**: 所有翻译资源集中管理，避免重复
5. **性能优良**: Context Provider只在顶层设置一次

#### 与其他方案对比
| 方案 | 优势 | 劣势 | 适用性 |
|------|------|------|--------|
| next-intl | Next.js官方推荐，SEO友好 | 依赖服务端渲染，Electron支持复杂 | ❌ 不适合Electron |
| react-i18next | 功能强大，生态完善 | 配置复杂，包体积较大 | ⚠️ 可用但偏重 |
| **React Context** | 简单灵活，完全可控 | 需要自己实现部分功能 | ✅ 最适合 |

### 3.2 架构设计

#### 文件结构
```
frontend/
├── messages/                    # 翻译资源目录
│   ├── en.json                  # 英文翻译
│   ├── zh-CN.json               # 简体中文翻译
│   └── electron.json            # Electron特有翻译
├── src/
│   ├── i18n/                    # 国际化系统核心
│   │   ├── index.ts             # 核心配置和语言检测
│   │   ├── context.tsx          # React Context Provider
│   │   ├── hook.ts              # useTranslations Hook
│   │   └── types.ts             # TypeScript类型定义
│   ├── app/                     # Next.js Web端入口
│   │   ├── layout.tsx           # Web端Layout包装i18n provider
│   │   └── (dashboard)/         # Web端页面
│   ├── client/                  # Electron端入口
│   │   ├── layout.tsx           # Electron端Layout包装i18n provider
│   │   └── pages/               # Electron端页面
│   ├── components/              # 共享UI组件
│   │   ├── ui/                  # 基础UI组件
│   │   ├── dashboard/           # 仪表板组件
│   │   ├── thread/              # 对话组件
│   │   └── ...                  # 其他组件
│   ├── lib/                     # 共享工具库
│   ├── hooks/                   # 共享React Hooks
│   └── providers/               # 共享Context Providers
├── electron/                    # Electron主进程
│   ├── main.js                  # 主进程代码
│   └── preload.js               # 预加载脚本
```

#### 核心组件关系图
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web App       │    │ Electron Client  │    │ Shared Components│
│   (app/)        │    │   (client/)      │    │  (components/)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                        │
         └───────────────────────┼────────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ I18n Provider   │
                    │ (i18n/context)  │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Translation     │
                    │ Resources       │
                    │ (messages/)     │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Electron Main   │
                    │ Process         │
                    │ (electron/main) │
                    └─────────────────┘
```

### 3.3 核心实现

#### 3.3.1 类型定义 (src/i18n/types.ts)
```typescript
export type Language = 'en' | 'zh-CN';
export type TranslationKey = string;
export type TranslationParams = Record<string, string | number>;

export interface TranslationResources {
  [key: string]: string | TranslationResources;
}

export interface I18nContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string, params?: TranslationParams) => string;
}

export interface ElectronAPI {
  getLocale?: () => string;
  setLanguage?: (lang: Language) => void;
  platform?: string;
  versions?: any;
}
```

#### 3.3.2 核心配置 (src/i18n/index.ts)
```typescript
import en from '../../messages/en.json';
import zhCN from '../../messages/zh-CN.json';
import electron from '../../messages/electron.json';
import type { Language, TranslationResources } from './types';

// 合并翻译资源
export const translations = {
  en: en as TranslationResources,
  'zh-CN': {
    ...zhCN as TranslationResources,
    // 合并Electron特有翻译
    electron: electron.en
  }
} as const;

export const defaultLanguage: Language = 'en';
export const supportedLanguages: Language[] = ['en', 'zh-CN'];

// 语言检测逻辑
export const detectLanguage = (): Language => {
  if (typeof window === 'undefined') return defaultLanguage;

  // Electron环境：优先使用系统语言
  if (window.electronAPI?.getLocale) {
    const systemLocale = window.electronAPI.getLocale();
    if (systemLocale?.startsWith('zh')) return 'zh-CN';
  }

  // Web环境：检测浏览器语言
  const browserLang = navigator.language || 'en';
  if (browserLang.startsWith('zh')) return 'zh-CN';

  // 检查本地存储的用户偏好
  const saved = localStorage.getItem('language') as Language;
  if (saved && supportedLanguages.includes(saved)) return saved;

  return defaultLanguage;
};

// 格式化翻译文本（支持参数插值）
export const formatTranslation = (
  template: string,
  params?: TranslationParams
): string => {
  if (!params) return template;

  return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
    return params[key]?.toString() || match;
  });
};

// 获取嵌套对象的翻译值
export const getNestedTranslation = (
  resources: TranslationResources,
  keys: string[]
): string | TranslationResources => {
  let current: TranslationResources | string = resources;

  for (const key of keys) {
    if (typeof current === 'object' && current && key in current) {
      current = current[key];
    } else {
      return keys[keys.length - 1]; // 回退到key
    }
  }

  return current;
};
```

#### 3.3.3 React Context Provider (src/i18n/context.tsx)
```typescript
'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { detectLanguage, formatTranslation, getNestedTranslation, translations } from './index';
import type { I18nContextType, Language, TranslationParams } from './types';

const I18nContext = createContext<I18nContextType | undefined>(undefined);

interface I18nProviderProps {
  children: ReactNode;
  defaultLang?: Language;
}

export function I18nProvider({ children, defaultLang }: I18nProviderProps) {
  const [language, setLanguageState] = useState<Language>(defaultLang || 'en');
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const detected = detectLanguage();
    setLanguageState(detected);
    setIsReady(true);
  }, []);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('language', lang);

    // Electron环境：通知主进程语言变更
    if (window.electronAPI?.setLanguage) {
      window.electronAPI.setLanguage(lang);
    }
  };

  const t = (key: string, params?: TranslationParams): string => {
    const keys = key.split('.');

    // 尝试获取当前语言的翻译
    let value = getNestedTranslation(translations[language], keys);

    // 如果找不到或不是字符串，回退到英文
    if (typeof value !== 'string') {
      value = getNestedTranslation(translations.en, keys);
      if (typeof value !== 'string') {
        return key; // 最终回退：返回key
      }
    }

    return formatTranslation(value as string, params);
  };

  // 确保语言检测完成后再渲染子组件
  if (!isReady) {
    return <div>Loading...</div>;
  }

  return (
    <I18nContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export const useI18n = (): I18nContextType => {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within I18nProvider');
  }
  return context;
};
```

#### 3.3.4 便捷Hook (src/i18n/hook.ts)
```typescript
export { useI18n } from './context';
export type { I18nContextType, Language, TranslationParams } from './types';
export { detectLanguage, translations, supportedLanguages } from './index';

// 便捷的格式化Hook
export const useTranslation = (namespace?: string) => {
  const { t } = useI18n();

  return {
    t: (key: string, params?: any) => {
      const fullKey = namespace ? `${namespace}.${key}` : key;
      return t(fullKey, params);
    }
  };
};
```

### 3.4 Electron特殊支持

#### 3.4.1 主进程菜单国际化 (electron/main.js)
```javascript
const { app, BrowserWindow, Menu, ipcMain } = require('electron');
const path = require('path');

// 菜单翻译资源
const menuTranslations = {
  en: {
    file: 'File',
    edit: 'Edit',
    view: 'View',
    window: 'Window',
    help: 'Help',
    quit: 'Quit',
    undo: 'Undo',
    redo: 'Redo',
    cut: 'Cut',
    copy: 'Copy',
    paste: 'Paste',
    selectAll: 'Select All',
    reload: 'Reload',
    forceReload: 'Force Reload',
    toggleDevTools: 'Toggle Developer Tools',
    resetZoom: 'Actual Size',
    zoomIn: 'Zoom In',
    zoomOut: 'Zoom Out',
    toggleFullscreen: 'Toggle Fullscreen',
    minimize: 'Minimize',
    close: 'Close',
    about: 'About Kortix',
    preferences: 'Preferences...',
    services: 'Services',
    hide: 'Hide Kortix',
    hideOthers: 'Hide Others',
    showAll: 'Show All'
  },
  'zh-CN': {
    file: '文件',
    edit: '编辑',
    view: '视图',
    window: '窗口',
    help: '帮助',
    quit: '退出',
    undo: '撤销',
    redo: '重做',
    cut: '剪切',
    copy: '复制',
    paste: '粘贴',
    selectAll: '全选',
    reload: '重新加载',
    forceReload: '强制重新加载',
    toggleDevTools: '切换开发者工具',
    resetZoom: '实际大小',
    zoomIn: '放大',
    zoomOut: '缩小',
    toggleFullscreen: '切换全屏',
    minimize: '最小化',
    close: '关闭',
    about: '关于 Kortix',
    preferences: '偏好设置...',
    services: '服务',
    hide: '隐藏 Kortix',
    hideOthers: '隐藏其他',
    showAll: '显示全部'
  }
};

let currentLanguage = 'en';

// 获取系统语言
function getSystemLanguage() {
  const locale = app.getLocale();
  return locale.startsWith('zh') ? 'zh-CN' : 'en';
}

// 创建应用菜单
function createMenu() {
  const t = menuTranslations[currentLanguage];

  const template = [
    {
      label: t.file,
      submenu: [
        process.platform === 'darwin' ? { role: 'about', label: t.about } : null,
        process.platform === 'darwin' ? { type: 'separator' } : null,
        { role: 'quit', label: t.quit }
      ].filter(Boolean)
    },
    {
      label: t.edit,
      submenu: [
        { role: 'undo', label: t.undo },
        { role: 'redo', label: t.redo },
        { type: 'separator' },
        { role: 'cut', label: t.cut },
        { role: 'copy', label: t.copy },
        { role: 'paste', label: t.paste },
        { role: 'selectAll', label: t.selectAll }
      ]
    },
    {
      label: t.view,
      submenu: [
        { role: 'reload', label: t.reload },
        { role: 'forceReload', label: t.forceReload },
        { role: 'toggleDevTools', label: t.toggleDevTools },
        { type: 'separator' },
        { role: 'resetZoom', label: t.resetZoom },
        { role: 'zoomIn', label: t.zoomIn },
        { role: 'zoomOut', label: t.zoomOut },
        { type: 'separator' },
        { role: 'toggleFullscreen', label: t.toggleFullscreen }
      ]
    },
    {
      label: t.window,
      submenu: [
        { role: 'minimize', label: t.minimize },
        { role: 'close', label: t.close }
      ]
    },
    {
      label: t.help,
      submenu: [
        { role: 'about', label: t.about }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// IPC通信处理
ipcMain.handle('get-system-locale', () => app.getLocale());
ipcMain.handle('set-menu-language', (event, language) => {
  currentLanguage = language;
  createMenu();
});

// 应用启动时初始化
app.whenReady().then(() => {
  currentLanguage = getSystemLanguage();
  createMenu();
  // ... 其他启动逻辑
});
```

#### 3.4.2 预加载脚本 (electron/preload.js)
```javascript
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // 基础信息
  platform: process.platform,
  versions: process.versions,

  // 国际化相关
  getLocale: () => ipcRenderer.invoke('get-system-locale'),
  setLanguage: (language) => ipcRenderer.invoke('set-menu-language', language),

  // 系统对话框
  showMessageBox: async (options) => {
    return ipcRenderer.invoke('show-message-box', options);
  },

  showOpenDialog: async (options) => {
    return ipcRenderer.invoke('show-open-dialog', options);
  },

  showSaveDialog: async (options) => {
    return ipcRenderer.invoke('show-save-dialog', options);
  },

  // 其他API
  showMessage: (message) => {
    ipcRenderer.invoke('show-message', message);
  }
});

// 环境变量暴露
contextBridge.exposeInMainWorld('process', {
  env: {
    NODE_ENV: process.env.NODE_ENV,
    ELECTRON_IS_DEV: process.env.ELECTRON_IS_DEV
  }
});
```

### 3.5 双入口适配

#### 3.5.1 Web端Layout (src/app/layout.tsx)
```typescript
import { ThemeProvider } from '@/components/home/theme-provider';
import { I18nProvider } from '@/i18n/context';
import { siteConfig } from '@/lib/site';
import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';
import { Toaster } from '@/components/ui/sonner';
import { detectLanguage } from '@/i18n';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  metadataBase: new URL(siteConfig.url),
  title: {
    default: siteConfig.name,
    template: `%s - ${siteConfig.name}`,
  },
  description: siteConfig.description,
  // ... 其他metadata配置
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // 在服务端检测语言
  const detectedLanguage = detectLanguage();

  return (
    <html lang={detectedLanguage} suppressHydrationWarning>
      <head>
        {/* Head内容 */}
      </head>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased font-sans bg-background`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <I18nProvider defaultLang={detectedLanguage}>
            <Providers>
              {children}
              <Toaster />
            </Providers>
          </I18nProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
```

#### 3.5.2 Electron端Layout (src/client/layout.tsx)
```typescript
'use client';

import { I18nProvider } from '@/i18n/context';
import { Providers } from '@/providers';
import { Toaster } from '@/components/ui/sonner';
import { ThemeProvider } from '@/components/home/theme-provider';
import { detectLanguage } from '@/i18n';

interface ElectronLayoutProps {
  children: React.ReactNode;
}

export default function ElectronLayout({ children }: ElectronLayoutProps) {
  const detectedLanguage = detectLanguage();

  return (
    <div className="h-screen w-full">
      <ThemeProvider
        attribute="class"
        defaultTheme="system"
        enableSystem
        disableTransitionOnChange
      >
        <I18nProvider defaultLang={detectedLanguage}>
          <Providers>
            {children}
            <Toaster />
          </Providers>
        </I18nProvider>
      </ThemeProvider>
    </div>
  );
}
```

## 4. 翻译资源管理

### 4.1 翻译文件规范

#### 4.1.1 英文翻译 (messages/en.json)
```json
{
  "dashboard": {
    "title": "What would you like to do today?",
    "placeholder": "Describe what you need help with...",
    "examples": {
      "research": "Research a topic",
      "analysis": "Analyze data",
      "automation": "Automate a task",
      "writing": "Write content",
      "coding": "Write or debug code"
    }
  },
  "common": {
    "save": "Save",
    "cancel": "Cancel",
    "confirm": "Confirm",
    "delete": "Delete",
    "edit": "Edit",
    "add": "Add",
    "remove": "Remove",
    "loading": "Loading...",
    "error": "Error",
    "success": "Success",
    "warning": "Warning",
    "info": "Information",
    "retry": "Retry",
    "close": "Close"
  },
  "navigation": {
    "dashboard": "Dashboard",
    "agents": "Agents",
    "playbooks": "Playbooks",
    "settings": "Settings",
    "billing": "Billing",
    "account": "Account",
    "help": "Help"
  },
  "auth": {
    "login": "Log In",
    "logout": "Log Out",
    "signup": "Sign Up",
    "email": "Email",
    "password": "Password",
    "forgotPassword": "Forgot Password?",
    "resetPassword": "Reset Password",
    "rememberMe": "Remember me"
  },
  "forms": {
    "required": "This field is required",
    "invalidEmail": "Please enter a valid email address",
    "passwordTooShort": "Password must be at least 8 characters",
    "passwordsNotMatch": "Passwords do not match"
  },
  "thread": {
    "newThread": "New Thread",
    "sendMessage": "Send Message",
    "attachFiles": "Attach Files",
    "voiceInput": "Voice Input",
    "stopGenerating": "Stop Generating",
    "regenerate": "Regenerate",
    "copy": "Copy",
    "share": "Share",
    "delete": "Delete"
  },
  "agents": {
    "createAgent": "Create Agent",
    "editAgent": "Edit Agent",
    "deleteAgent": "Delete Agent",
    "agentName": "Agent Name",
    "agentDescription": "Agent Description",
    "agentModel": "Agent Model",
    "agentTools": "Agent Tools",
    "agentSettings": "Agent Settings"
  },
  "billing": {
    "subscription": "Subscription",
    "usage": "Usage",
    "upgrade": "Upgrade",
    "downgrade": "Downgrade",
    "cancelSubscription": "Cancel Subscription",
    "paymentMethod": "Payment Method",
    "billingHistory": "Billing History"
  },
  "errors": {
    "networkError": "Network error occurred",
    "serverError": "Server error occurred",
    "unauthorized": "You are not authorized",
    "forbidden": "Access forbidden",
    "notFound": "Page not found",
    "somethingWentWrong": "Something went wrong"
  }
}
```

#### 4.1.2 中文翻译 (messages/zh-CN.json)
```json
{
  "dashboard": {
    "title": "今天想做什么？",
    "placeholder": "描述你需要帮助的事项...",
    "examples": {
      "research": "研究一个主题",
      "analysis": "分析数据",
      "automation": "自动化任务",
      "writing": "撰写内容",
      "coding": "编写或调试代码"
    }
  },
  "common": {
    "save": "保存",
    "cancel": "取消",
    "confirm": "确认",
    "delete": "删除",
    "edit": "编辑",
    "add": "添加",
    "remove": "移除",
    "loading": "加载中...",
    "error": "错误",
    "success": "成功",
    "warning": "警告",
    "info": "信息",
    "retry": "重试",
    "close": "关闭"
  },
  "navigation": {
    "dashboard": "仪表板",
    "agents": "代理",
    "playbooks": "剧本",
    "settings": "设置",
    "billing": "账单",
    "account": "账户",
    "help": "帮助"
  },
  "auth": {
    "login": "登录",
    "logout": "退出",
    "signup": "注册",
    "email": "邮箱",
    "password": "密码",
    "forgotPassword": "忘记密码？",
    "resetPassword": "重置密码",
    "rememberMe": "记住我"
  },
  "forms": {
    "required": "此字段为必填项",
    "invalidEmail": "请输入有效的邮箱地址",
    "passwordTooShort": "密码至少需要8个字符",
    "passwordsNotMatch": "两次输入的密码不匹配"
  },
  "thread": {
    "newThread": "新对话",
    "sendMessage": "发送消息",
    "attachFiles": "附加文件",
    "voiceInput": "语音输入",
    "stopGenerating": "停止生成",
    "regenerate": "重新生成",
    "copy": "复制",
    "share": "分享",
    "delete": "删除"
  },
  "agents": {
    "createAgent": "创建代理",
    "editAgent": "编辑代理",
    "deleteAgent": "删除代理",
    "agentName": "代理名称",
    "agentDescription": "代理描述",
    "agentModel": "代理模型",
    "agentTools": "代理工具",
    "agentSettings": "代理设置"
  },
  "billing": {
    "subscription": "订阅",
    "usage": "使用情况",
    "upgrade": "升级",
    "downgrade": "降级",
    "cancelSubscription": "取消订阅",
    "paymentMethod": "支付方式",
    "billingHistory": "账单历史"
  },
  "errors": {
    "networkError": "网络错误",
    "serverError": "服务器错误",
    "unauthorized": "未授权",
    "forbidden": "访问被禁止",
    "notFound": "页面未找到",
    "somethingWentWrong": "出现了问题"
  }
}
```

#### 4.1.3 Electron特有翻译 (messages/electron.json)
```json
{
  "en": {
    "menu": {
      "file": "File",
      "edit": "Edit",
      "view": "View",
      "window": "Window",
      "help": "Help",
      "quit": "Quit",
      "about": "About Kortix",
      "preferences": "Preferences"
    },
    "dialog": {
      "confirmExit": "Are you sure you want to exit?",
      "unsavedChanges": "You have unsaved changes. Do you want to continue?",
      "confirmDelete": "Are you sure you want to delete this item?",
      "operationSuccess": "Operation completed successfully",
      "operationFailed": "Operation failed"
    },
    "notification": {
      "updateAvailable": "A new version is available",
      "updateDownloaded": "Update downloaded, restart to apply",
      "updateError": "Update download failed"
    }
  },
  "zh-CN": {
    "menu": {
      "file": "文件",
      "edit": "编辑",
      "view": "视图",
      "window": "窗口",
      "help": "帮助",
      "quit": "退出",
      "about": "关于 Kortix",
      "preferences": "偏好设置"
    },
    "dialog": {
      "confirmExit": "确定要退出吗？",
      "unsavedChanges": "您有未保存的更改，要继续吗？",
      "confirmDelete": "确定要删除此项目吗？",
      "operationSuccess": "操作完成",
      "operationFailed": "操作失败"
    },
    "notification": {
      "updateAvailable": "新版本可用",
      "updateDownloaded": "更新已下载，重启以应用",
      "updateError": "更新下载失败"
    }
  }
}
```

### 4.2 翻译命名规范

#### 4.2.1 命名规则
- **层级结构**: 使用点号分隔的命名空间，如 `dashboard.title`
- **小写字母**: 所有key使用小写字母
- **描述性**: key名称应清晰描述翻译内容
- **一致性**: 同类型功能使用相同前缀

#### 4.2.2 命名空间约定
- `dashboard.*`: 仪表板相关文本
- `common.*`: 通用文本（按钮、状态等）
- `navigation.*`: 导航菜单文本
- `auth.*`: 认证相关文本
- `forms.*`: 表单验证和标签
- `thread.*`: 对话相关文本
- `agents.*`: 代理管理相关文本
- `billing.*`: 账单和订阅相关文本
- `errors.*`: 错误信息
- `electron.*`: Electron特有文本

## 5. 使用示例

### 5.1 基础组件翻译

#### 5.1.1 仪表板组件 (src/components/dashboard/dashboard-content.tsx)
```typescript
'use client';

import { useI18n } from '@/i18n/context';
import { ChatInput } from '@/components/thread/chat-input/chat-input';
import { Examples } from './examples';

export function DashboardContent() {
  const { t } = useI18n();

  return (
    <div className="flex flex-col h-screen w-full">
      <div className="flex-1 flex items-center justify-center px-4 py-8">
        <div className="w-full max-w-[650px] flex flex-col items-center space-y-6">
          <div className="flex flex-col items-center text-center w-full">
            <p className="tracking-tight text-2xl md:text-3xl font-normal text-foreground/90">
              {t('dashboard.title')}
            </p>
          </div>

          <div className="w-full">
            <ChatInput
              placeholder={t('dashboard.placeholder')}
              // ... other props
            />
          </div>

          <div className="w-full">
            <Examples onSelectPrompt={() => {}} count={4} />
          </div>
        </div>
      </div>
    </div>
  );
}
```

#### 5.1.2 语言选择器组件 (src/components/language-selector.tsx)
```typescript
'use client';

import { useI18n, supportedLanguages } from '@/i18n';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Globe } from 'lucide-react';

const languageNames = {
  en: 'English',
  'zh-CN': '简体中文'
};

export function LanguageSelector() {
  const { language, setLanguage } = useI18n();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm">
          <Globe className="h-4 w-4 mr-2" />
          {languageNames[language]}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {supportedLanguages.map((lang) => (
          <DropdownMenuItem
            key={lang}
            onClick={() => setLanguage(lang)}
            className={language === lang ? 'bg-accent' : ''}
          >
            {languageNames[lang]}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

#### 5.1.3 带参数的翻译
```typescript
// 翻译文件中
{
  "agents": {
    "deleteConfirm": "Are you sure you want to delete agent '{{name}}'?",
    "agentCount": "You have {{count}} agent(s)"
  }
}

// 组件中使用
const { t } = useI18n();
const confirmMessage = t('agents.deleteConfirm', { name: agentName });
const countMessage = t('agents.agentCount', { count: agents.length });
```

### 5.2 复杂组件翻译

#### 5.2.1 表单组件翻译
```typescript
// src/components/auth/login-form.tsx
'use client';

import { useI18n } from '@/i18n/context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export function LoginForm() {
  const { t } = useI18n();

  return (
    <form className="space-y-4">
      <div>
        <label htmlFor="email">{t('auth.email')}</label>
        <Input id="email" type="email" />
      </div>

      <div>
        <label htmlFor="password">{t('auth.password')}</label>
        <Input id="password" type="password" />
      </div>

      <Button type="submit">
        {t('auth.login')}
      </Button>
    </form>
  );
}
```

#### 5.2.2 Electron特有组件
```typescript
// src/components/electron/system-dialog.tsx
'use client';

import { useI18n } from '@/i18n/context';
import { useElectronAPI } from '@/hooks/use-electron';

export function SystemDialog() {
  const { t } = useI18n();
  const { showMessageBox } = useElectronAPI();

  const handleConfirmExit = async () => {
    const result = await showMessageBox({
      type: 'question',
      buttons: [t('common.confirm'), t('common.cancel')],
      defaultId: 1,
      message: t('electron.dialog.confirmExit'),
      detail: t('electron.dialog.unsavedChanges')
    });

    if (result.response === 0) {
      // 用户确认退出
      window.close();
    }
  };

  return (
    <Button onClick={handleConfirmExit}>
      {t('common.quit')}
    </Button>
  );
}
```

## 6. 性能优化

### 6.1 代码分割
- **按语言加载**: 只加载当前语言的翻译文件
- **组件懒加载**: 结合React.lazy实现组件级别的代码分割
- **翻译缓存**: 将翻译内容缓存在内存中

### 6.2 包大小优化
- **Tree Shaking**: 确保未使用的翻译内容不会被打包
- **压缩**: 在生产环境中压缩翻译文件
- **CDN**: 大型翻译资源可通过CDN加载

### 6.3 运行时优化
- **Memoization**: 缓存翻译结果，避免重复计算
- **批量更新**: 语言切换时批量更新UI
- **异步加载**: 翻译文件异步加载，不阻塞初始化

## 7. 测试策略

### 7.1 单元测试
```typescript
// src/i18n/__tests__/context.test.tsx
import { render, screen } from '@testing-library/react';
import { I18nProvider, useI18n } from '../context';

describe('I18n Context', () => {
  it('provides translation function', () => {
    const TestComponent = () => {
      const { t } = useI18n();
      return <div>{t('dashboard.title')}</div>;
    };

    render(
      <I18nProvider>
        <TestComponent />
      </I18nProvider>
    );

    expect(screen.getByText('What would you like to do today?')).toBeInTheDocument();
  });

  it('falls back to English when translation missing', () => {
    const TestComponent = () => {
      const { t } = useI18n();
      return <div>{t('nonexistent.key')}</div>;
    };

    render(
      <I18nProvider defaultLang="zh-CN">
        <TestComponent />
      </I18nProvider>
    );

    expect(screen.getByText('nonexistent.key')).toBeInTheDocument();
  });
});
```

### 7.2 集成测试
- **语言切换测试**: 验证语言切换功能正常工作
- **参数插值测试**: 验证翻译参数替换正确
- **回退机制测试**: 验证翻译缺失时的回退逻辑

### 7.3 E2E测试
- **端到端语言切换**: 使用Playwright测试完整用户流程
- **Electron集成测试**: 测试Electron环境下的i18n功能
- **性能测试**: 测试大型翻译文件的加载性能

## 8. 部署和维护

### 8.1 构建配置
```typescript
// next.config.ts
const withTM = require('next-transpile-modules')(['@/i18n']);

const nextConfig = {
  // ... 其他配置
  webpack: (config) => {
    // 确保翻译文件被正确处理
    config.resolve.extensions.push('.json');
    return config;
  },
};

module.exports = withTM(nextConfig);
```

### 8.2 持续集成
- **翻译检查**: 在CI中检查翻译文件的完整性
- **类型检查**: 确保翻译键的类型安全
- **自动化测试**: 自动运行i18n相关测试

### 8.3 维护策略
- **翻译更新流程**: 建立翻译文件的更新和审核流程
- **版本控制**: 翻译文件版本化，支持回滚
- **监控**: 监控翻译缺失和错误情况

## 9. 扩展规划

### 9.1 多语言扩展
- **RTL语言支持**: 为阿拉伯语、希伯来语等RTL语言做准备
- **复数形式处理**: 支持不同语言的复数规则
- **日期时间本地化**: 支持不同地区的日期时间格式

### 9.2 高级功能
- **翻译管理后台**: 开发翻译管理的Web界面
- **协作翻译**: 支持多人协作翻译工作流
- **翻译质量检查**: 自动检查翻译质量和一致性

### 9.3 性能监控
- **翻译性能监控**: 监控翻译加载和渲染性能
- **用户行为分析**: 分析用户语言偏好和使用模式
- **A/B测试**: 测试不同翻译版本的效果

## 10. 总结

本技术方案提供了一个完整、灵活、可扩展的国际化解决方案，特别适合Kortix应用的双入口架构。通过基于React Context的统一i18n系统，我们实现了：

1. **代码高度共享**: Web端和Electron端共享翻译系统和资源
2. **原生支持**: Electron菜单、对话框等原生元素完全支持中文
3. **开发友好**: 简单易用的API，类型安全，良好的开发体验
4. **性能优良**: 按需加载，缓存优化，最小化性能影响
5. **易于维护**: 清晰的文件结构，规范的命名约定，完善的测试覆盖

该方案为Kortix应用的国际化奠定了坚实的基础，不仅满足了当前中文支持的需求，也为未来多语言扩展做好了准备。