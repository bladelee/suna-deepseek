# Kortix 应用中文化功能测试验证方案

## 1. 测试概述

### 1.1 测试目标
确保Kortix应用的国际化(i18n)功能完整可靠，验证中英文双语切换功能正常工作，用户体验流畅，无功能回归。

### 1.2 测试范围
- **Web端功能测试**: Next.js应用的i18n功能
- **Electron端功能测试**: 桌面应用的i18n功能
- **共享组件测试**: 共用组件的翻译效果
- **性能测试**: i18n对应用性能的影响
- **兼容性测试**: 不同环境下的兼容性

### 1.3 测试策略
- **分层测试**: 单元测试 + 集成测试 + E2E测试
- **多环境验证**: 开发环境 + 测试环境 + 生产环境
- **多平台验证**: Windows + macOS + Linux
- **多浏览器验证**: Chrome + Firefox + Safari + Edge

## 2. 测试环境准备

### 2.1 测试环境配置

#### 开发环境
```bash
# 前置条件
- Node.js 18+
- npm 或 yarn
- Git
- 代码编辑器 (推荐 VS Code)

# 环境搭建
git clone [repository-url]
cd frontend
npm install
npm run dev  # 启动开发服务器

# Electron开发环境
npm run electron:dev
```

#### 测试环境
```bash
# 构建测试版本
npm run build
npm run start  # 生产模式测试

# Electron测试版本
npm run electron:build
npm run electron:dist
```

### 2.2 测试数据准备

#### 翻译完整性检查脚本
```javascript
// scripts/check-translations.js
const fs = require('fs');
const path = require('path');

// 读取翻译文件
const enTranslations = require('../messages/en.json');
const zhTranslations = require('../messages/zh-CN.json');

// 检查翻译完整性
function checkTranslationCompleteness() {
  const missingKeys = [];
  const extraKeys = [];

  function checkKeys(obj1, obj2, prefix = '') {
    for (const key in obj1) {
      const fullKey = prefix ? `${prefix}.${key}` : key;

      if (!(key in obj2)) {
        missingKeys.push(fullKey);
      } else if (typeof obj1[key] === 'object' && typeof obj2[key] === 'object') {
        checkKeys(obj1[key], obj2[key], fullKey);
      }
    }

    for (const key in obj2) {
      const fullKey = prefix ? `${prefix}.${key}` : key;

      if (!(key in obj1)) {
        extraKeys.push(fullKey);
      }
    }
  }

  checkKeys(enTranslations, zhTranslations);

  return {
    missingKeys,
    extraKeys,
    completeness: ((Object.keys(enTranslations).length - missingKeys.length) / Object.keys(enTranslations).length * 100).toFixed(2)
  };
}

// 检查参数占位符
function checkPlaceholders() {
  const placeholderRegex = /\{\{(\w+)\}\}/g;
  const issues = [];

  function checkPlaceholdersInObject(obj, prefix = '') {
    for (const key in obj) {
      const fullKey = prefix ? `${prefix}.${key}` : key;

      if (typeof obj[key] === 'string') {
        const enPlaceholders = (enTranslations[fullKey] || '').match(placeholderRegex) || [];
        const zhPlaceholders = (zhTranslations[fullKey] || '').match(placeholderRegex) || [];

        if (enPlaceholders.length !== zhPlaceholders.length) {
          issues.push({
            key: fullKey,
            issue: 'Placeholder count mismatch',
            en: enPlaceholders,
            zh: zhPlaceholders
          });
        }
      } else if (typeof obj[key] === 'object') {
        checkPlaceholdersInObject(obj[key], fullKey);
      }
    }
  }

  checkPlaceholdersInObject(enTranslations);
  return issues;
}

module.exports = { checkTranslationCompleteness, checkPlaceholders };
```

#### 测试数据生成器
```javascript
// scripts/generate-test-data.js
const fs = require('fs');

// 生成测试用户数据
function generateTestUsers() {
  return [
    {
      id: 'test-user-1',
      email: 'test@example.com',
      name: 'Test User',
      preferredLanguage: 'zh-CN'
    },
    {
      id: 'test-user-2',
      email: 'test2@example.com',
      name: 'Test User 2',
      preferredLanguage: 'en'
    }
  ];
}

// 生成测试代理数据
function generateTestAgents() {
  return [
    {
      id: 'agent-1',
      name: '研究助手',
      description: '帮助进行学术研究和数据分析',
      model: 'gpt-4',
      tools: ['web-search', 'file-analysis']
    },
    {
      id: 'agent-2',
      name: 'Code Helper',
      description: 'Assists with coding and debugging',
      model: 'claude-3',
      tools: ['code-execution', 'web-search']
    }
  ];
}

// 生成测试对话数据
function generateTestThreads() {
  return [
    {
      id: 'thread-1',
      title: '市场研究分析',
      messages: [
        { role: 'user', content: '请帮我分析当前的市场趋势' },
        { role: 'assistant', content: '我来为您分析最新的市场数据和趋势...' }
      ]
    },
    {
      id: 'thread-2',
      title: 'Code Review Request',
      messages: [
        { role: 'user', content: 'Please review this React component' },
        { role: 'assistant', content: 'I\'ll help you review this React component...' }
      ]
    }
  ];
}

module.exports = { generateTestUsers, generateTestAgents, generateTestThreads };
```

## 3. 测试用例设计

### 3.1 功能测试用例

#### 3.1.1 基础i18n功能测试

**TC-001: 语言检测功能测试**
```gherkin
Feature: 语言检测功能
  作为一个用户
  我希望应用能自动检测我的语言偏好
  以便使用我熟悉的语言界面

Scenario: Web环境自动语言检测
  Given 我是一个新用户，首次访问Web应用
  When 我的浏览器语言设置为中文
  Then 应用应该自动显示中文界面
  And HTML lang属性应该设置为"zh-CN"

Scenario: Electron环境自动语言检测
  Given 我是一个新用户，首次启动Electron应用
  When 我的系统语言设置为中文
  Then 应用应该自动显示中文界面
  And 菜单应该显示为中文

Scenario: 用户偏好记忆
  Given 我之前设置过语言偏好为中文
  When 我重新访问应用
  Then 应用应该记住我的偏好并显示中文界面
  And localStorage应该保存语言设置
```

**TC-002: 语言切换功能测试**
```gherkin
Feature: 语言切换功能
  作为一个用户
  我希望能随时切换界面语言
  以便使用不同语言版本

Scenario: Web端语言切换
  Given 我在Web应用的仪表板页面
  When 我点击语言选择器并选择"简体中文"
  Then 页面所有文本应该立即切换为中文
  And 语言选择器应该显示当前选中的语言
  And 页面不应该重新加载

Scenario: Electron端语言切换
  Given 我在Electron应用的任意页面
  When 我点击语言选择器并选择"简体中文"
  Then 页面所有文本应该立即切换为中文
  And 应用菜单应该同步更新为中文
  And 语言偏好应该被保存

Scenario: 语言切换持久化
  Given 我将语言切换为中文
  When 我关闭并重新打开应用
  Then 应用应该保持中文界面
  And 不应该显示语言切换前的默认语言
```

**TC-003: 翻译内容正确性测试**
```gherkin
Feature: 翻译内容验证
  作为一个中文用户
  我希望所有翻译内容准确且符合中文表达习惯
  以便获得良好的用户体验

Scenario: 主要页面翻译验证
  Given 我选择中文界面
  When 我访问仪表板页面
  Then 页面标题应该显示"今天想做什么？"
  And 输入框占位符应该显示中文提示
  And 所有按钮和链接都应该显示中文

Scenario: 导航菜单翻译验证
  Given 我选择中文界面
  When 我查看侧边栏导航
  Then 所有菜单项都应该显示中文
  And 图标提示文本应该是中文
  And 用户菜单项应该是中文

Scenario: 表单翻译验证
  Given 我选择中文界面
  When 我访问登录页面
  Then 所有表单标签应该是中文
  And 按钮文本应该是中文
  And 验证错误消息应该是中文
```

### 3.2 Electron特有功能测试

**TC-004: Electron菜单国际化测试**
```gherkin
Feature: Electron菜单国际化
  作为一个Electron应用用户
  我希望应用菜单显示为我的首选语言
  以便更好地使用应用功能

Scenario: 主菜单翻译验证
  Given 我在Electron应用中选择中文界面
  When 我查看应用菜单
  Then "文件"菜单应该包含中文选项
  And "编辑"菜单应该包含中文选项
  And "视图"菜单应该包含中文选项
  And "帮助"菜单应该包含中文选项

Scenario: 快捷键显示
  Given 我在中文界面下
  When 我查看菜单项
  Then 快捷键应该正确显示 (如 "Ctrl+C")
  And 快捷键应该与系统标准一致

Scenario: 平台特定菜单
  Given 我在macOS系统下使用中文界面
  When 我查看应用菜单
  Then 应该显示macOS特有的菜单项
  And 所有菜单项都应该是中文
```

**TC-005: 系统对话框翻译测试**
```gherkin
Feature: 系统对话框翻译
  作为一个用户
  我希望系统对话框显示为我的首选语言
  以便理解对话框内容

Scenario: 确认对话框翻译
  Given 我在中文界面下
  When 应用显示确认对话框
  Then 对话框标题和内容应该是中文
  And 按钮文本应该是中文
  And 默认焦点应该正确设置

Scenario: 文件选择对话框
  Given 我在中文界面下
  When 我触发文件选择功能
  Then 系统文件选择对话框应该正常打开
  And 应用相关的提示信息应该是中文
```

### 3.3 性能测试用例

**TC-006: 启动性能测试**
```gherkin
Feature: 应用启动性能
  作为一个用户
  我希望i18n功能不会显著影响应用启动速度
  以便快速开始使用应用

Scenario: Web应用启动时间
  Given 我清除了浏览器缓存
  When 我首次访问Web应用
  Then 应用启动时间不应该超过3秒
  And 翻译资源加载时间不应该超过500ms

Scenario: Electron应用启动时间
  Given 我没有运行Electron应用
  When 我启动Electron应用
  Then 应用启动时间不应该超过5秒
  And 中文界面应该在启动后立即可用

Scenario: 语言切换响应时间
  Given 我在应用的任意页面
  When 我切换语言
  Then 界面更新应该在300ms内完成
  And 不应该有明显的卡顿
```

### 3.4 兼容性测试用例

**TC-007: 浏览器兼容性测试**
```gherkin
Feature: 浏览器兼容性
  作为一个用户
  我希望在不同浏览器中都能正常使用i18n功能
  以便在我偏好的浏览器中使用应用

Scenario: Chrome浏览器测试
  Given 我使用Chrome浏览器最新版本
  When 我访问Web应用
  Then 所有i18n功能应该正常工作
  And 中文显示应该正确
  And 语言切换应该流畅

Scenario: Safari浏览器测试
  Given 我使用Safari浏览器最新版本
  When 我访问Web应用
  Then 所有i18n功能应该正常工作
  And 中文字体应该渲染正确

Scenario: 移动端浏览器测试
  Given 我使用移动端浏览器
  When 我访问Web应用
  Then i18n功能应该在移动端正常工作
  And 界面应该适配移动屏幕
```

## 4. 自动化测试实现

### 4.1 单元测试

#### i18n核心功能单元测试
```typescript
// src/i18n/__tests__/index.test.ts
import { detectLanguage, formatTranslation, getNestedTranslation } from '../index';
import { translations } from '../index';

describe('i18n Core Functions', () => {
  describe('detectLanguage', () => {
    beforeEach(() => {
      // Mock localStorage
      Object.defineProperty(window, 'localStorage', {
        value: {
          getItem: jest.fn(),
          setItem: jest.fn(),
        },
        writable: true,
      });

      // Mock navigator
      Object.defineProperty(window, 'navigator', {
        value: {
          language: 'en-US',
        },
        writable: true,
      });

      // Mock electronAPI
      Object.defineProperty(window, 'electronAPI', {
        value: undefined,
        writable: true,
      });
    });

    it('should detect Chinese browser language', () => {
      (window.navigator as any).language = 'zh-CN';
      expect(detectLanguage()).toBe('zh-CN');
    });

    it('should detect Chinese system locale in Electron', () => {
      (window as any).electronAPI = {
        getLocale: () => 'zh-CN',
      };
      expect(detectLanguage()).toBe('zh-CN');
    });

    it('should return saved language preference', () => {
      (window.localStorage as any).getItem.mockReturnValue('zh-CN');
      expect(detectLanguage()).toBe('zh-CN');
    });

    it('should fallback to English for unsupported languages', () => {
      (window.navigator as any).language = 'fr-FR';
      expect(detectLanguage()).toBe('en');
    });
  });

  describe('formatTranslation', () => {
    it('should format translation with parameters', () => {
      const template = 'Hello {{name}}, you have {{count}} messages';
      const params = { name: 'John', count: 5 };
      expect(formatTranslation(template, params)).toBe('Hello John, you have 5 messages');
    });

    it('should handle missing parameters', () => {
      const template = 'Hello {{name}}, you have {{count}} messages';
      const params = { name: 'John' };
      expect(formatTranslation(template, params)).toBe('Hello John, you have {{count}} messages');
    });

    it('should handle empty template', () => {
      expect(formatTranslation('', {})).toBe('');
    });

    it('should handle no parameters', () => {
      const template = 'Hello World';
      expect(formatTranslation(template)).toBe('Hello World');
    });
  });

  describe('getNestedTranslation', () => {
    it('should get nested translation', () => {
      const resources = {
        dashboard: {
          title: 'What would you like to do today?',
          examples: {
            research: 'Research a topic',
          },
        },
      };

      expect(getNestedTranslation(resources, ['dashboard', 'title']))
        .toBe('What would you like to do today?');
      expect(getNestedTranslation(resources, ['dashboard', 'examples', 'research']))
        .toBe('Research a topic');
    });

    it('should return key when translation not found', () => {
      const resources = {};
      expect(getNestedTranslation(resources, ['nonexistent', 'key']))
        .toBe('key');
    });

    it('should handle empty key array', () => {
      const resources = { test: 'value' };
      expect(getNestedTranslation(resources, []))
        .toBe(resources);
    });
  });
});
```

#### Context Provider单元测试
```typescript
// src/i18n/__tests__/context.test.tsx
import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { I18nProvider, useI18n } from '../context';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock electronAPI
Object.defineProperty(window, 'electronAPI', {
  value: {
    setLanguage: jest.fn(),
  },
  writable: true,
});

describe('I18nProvider', () => {
  beforeEach(() => {
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
  });

  it('should provide translation function', () => {
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

  it('should switch language', () => {
    const TestComponent = () => {
      const { t, language, setLanguage } = useI18n();
      return (
        <div>
          <span data-testid="language">{language}</span>
          <span>{t('dashboard.title')}</span>
          <button onClick={() => setLanguage('zh-CN')}>Switch to Chinese</button>
        </div>
      );
    };

    render(
      <I18nProvider>
        <TestComponent />
      </I18nProvider>
    );

    // Initial state should be English
    expect(screen.getByTestId('language')).toHaveTextContent('en');
    expect(screen.getByText('What would you like to do today?')).toBeInTheDocument();

    // Switch to Chinese
    act(() => {
      fireEvent.click(screen.getByText('Switch to Chinese'));
    });

    // Should switch to Chinese
    expect(screen.getByTestId('language')).toHaveTextContent('zh-CN');
    expect(screen.getByText('今天想做什么？')).toBeInTheDocument();
    expect(localStorageMock.setItem).toHaveBeenCalledWith('language', 'zh-CN');
    expect(window.electronAPI.setLanguage).toHaveBeenCalledWith('zh-CN');
  });

  it('should fallback to English for missing translations', () => {
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

  it('should handle parameter interpolation', () => {
    const TestComponent = () => {
      const { t } = useI18n();
      return (
        <div>
          {t('agents.deleteConfirm', { name: 'Test Agent' })}
        </div>
      );
    };

    render(
      <I18nProvider>
        <TestComponent />
      </I18nProvider>
    );

    expect(screen.getByText('Are you sure you want to delete agent \'Test Agent\'?')).toBeInTheDocument();
  });

  it('should throw error when useI18n is used outside provider', () => {
    const TestComponent = () => {
      const { t } = useI18n();
      return <div>{t('test')}</div>;
    };

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useI18n must be used within I18nProvider');
  });
});
```

### 4.2 集成测试

#### 组件翻译集成测试
```typescript
// src/components/__tests__/dashboard-i18n.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { I18nProvider } from '@/i18n/context';
import { DashboardContent } from '../dashboard/dashboard-content';

// Mock dependencies
jest.mock('@/hooks/react-query/agents/use-agents', () => ({
  useAgents: () => ({
    data: {
      agents: [
        {
          agent_id: 'agent-1',
          name: 'Research Assistant',
          metadata: { is_suna_default: true },
        },
      ],
    },
  }),
}));

jest.mock('@/hooks/use-accounts', () => ({
  useAccounts: () => ({
    data: [
      {
        account_id: 'account-1',
        personal_account: true,
      },
    ],
  }),
}));

jest.mock('@/lib/api', () => ({
  BillingError: class extends Error {},
  AgentRunLimitError: class extends Error {},
}));

jest.mock('@/components/billing/billing-modal', () => ({
  BillingModal: ({ open, onOpenChange }) => (
    open ? <div data-testid="billing-modal">Billing Modal</div> : null
  ),
}));

jest.mock('@/components/billing/usage-limit-alert', () => ({
  BillingErrorAlert: () => <div data-testid="billing-alert">Billing Alert</div>,
}));

describe('Dashboard i18n Integration', () => {
  const renderWithI18n = (component, { defaultLang = 'en' } = {}) => {
    return render(
      <I18nProvider defaultLang={defaultLang}>
        {component}
      </I18nProvider>
    );
  };

  it('should display English dashboard by default', () => {
    renderWithI18n(<DashboardContent />);

    expect(screen.getByText('What would you like to do today?')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Describe what you need help with...')).toBeInTheDocument();
  });

  it('should display Chinese dashboard when language is set to zh-CN', () => {
    renderWithI18n(<DashboardContent />, { defaultLang: 'zh-CN' });

    expect(screen.getByText('今天想做什么？')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('描述你需要帮助的事项...')).toBeInTheDocument();
  });

  it('should switch language when language selector is used', async () => {
    renderWithI18n(<DashboardContent />);

    // Initially English
    expect(screen.getByText('What would you like to do today?')).toBeInTheDocument();

    // Find and click language selector (assuming it exists in the dashboard)
    const languageSelector = screen.getByRole('combobox');
    fireEvent.change(languageSelector, { target: { value: 'zh-CN' } });

    // Wait for language change
    await waitFor(() => {
      expect(screen.getByText('今天想做什么？')).toBeInTheDocument();
    });
  });

  it('should maintain functionality after language switch', async () => {
    renderWithI18n(<DashboardContent />);

    const chatInput = screen.getByPlaceholderText('Describe what you need help with...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    // Test functionality in English
    fireEvent.change(chatInput, { target: { value: 'Test message' } });
    expect(chatInput).toHaveValue('Test message');

    // Switch language
    const languageSelector = screen.getByRole('combobox');
    fireEvent.change(languageSelector, { target: { value: 'zh-CN' } });

    await waitFor(() => {
      expect(screen.getByPlaceholderText('描述你需要帮助的事项...')).toBeInTheDocument();
    });

    // Test functionality in Chinese
    const chineseInput = screen.getByPlaceholderText('描述你需要帮助的事项...');
    expect(chineseInput).toHaveValue('Test message'); // Value should be preserved
  });

  it('should handle error messages in different languages', async () => {
    // Mock error scenario
    const mockError = new Error('Network error occurred');
    jest.spyOn(console, 'error').mockImplementation(() => {});

    renderWithI18n(<DashboardContent />, { defaultLang: 'zh-CN' });

    // Trigger error scenario (this would depend on actual component implementation)
    // For example, submitting a message that fails
    const chatInput = screen.getByPlaceholderText('描述你需要帮助的事项...');
    const sendButton = screen.getByRole('button', { name: /发送/i });

    fireEvent.change(chatInput, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);

    // Wait for error message to appear (in Chinese)
    await waitFor(() => {
      // This depends on how errors are displayed in the actual component
      // expect(screen.getByText('网络错误')).toBeInTheDocument();
    });
  });
});
```

### 4.3 E2E测试

#### Playwright E2E测试配置
```typescript
// tests/e2e/i18n.spec.ts
import { test, expect } from '@playwright/test';

test.describe('i18n E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Wait for app to load
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
  });

  test('should auto-detect browser language', async ({ page, context }) => {
    // Set browser language to Chinese
    await context.addInitScript(() => {
      Object.defineProperty(navigator, 'language', {
        get: () => 'zh-CN',
      });
    });

    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    // Should display Chinese interface
    await expect(page.locator('text=今天想做什么？')).toBeVisible();
    await expect(page.locator('text=描述你需要帮助的事项...')).toBeVisible();
  });

  test('should switch language from English to Chinese', async ({ page }) => {
    // Should start with English
    await expect(page.locator('text=What would you like to do today?')).toBeVisible();

    // Find and click language selector
    const languageSelector = page.locator('[data-testid="language-selector"]');
    await languageSelector.click();

    // Select Chinese
    const chineseOption = page.locator('text=简体中文');
    await chineseOption.click();

    // Should switch to Chinese
    await expect(page.locator('text=今天想做什么？')).toBeVisible();
    await expect(page.locator('text=描述你需要帮助的事项...')).toBeVisible();
  });

  test('should persist language preference across page reloads', async ({ page }) => {
    // Switch to Chinese
    const languageSelector = page.locator('[data-testid="language-selector"]');
    await languageSelector.click();
    await page.locator('text=简体中文').click();

    // Verify Chinese interface
    await expect(page.locator('text=今天想做什么？')).toBeVisible();

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Should still be in Chinese
    await expect(page.locator('text=今天想做什么？')).toBeVisible();
  });

  test('should translate all major sections', async ({ page }) => {
    // Switch to Chinese
    const languageSelector = page.locator('[data-testid="language-selector"]');
    await languageSelector.click();
    await page.locator('text=简体中文').click();

    // Check dashboard
    await expect(page.locator('text=今天想做什么？')).toBeVisible();

    // Check sidebar navigation
    await expect(page.locator('text=仪表板')).toBeVisible();
    await expect(page.locator('text=代理')).toBeVisible();
    await expect(page.locator('text=设置')).toBeVisible();

    // Check buttons and interactions
    const sendButton = page.locator('button:has-text("发送")');
    await expect(sendButton).toBeVisible();
  });

  test('should handle forms in different languages', async ({ page }) => {
    // Navigate to login page (assuming it exists)
    await page.goto('http://localhost:3000/login');
    await page.waitForLoadState('networkidle');

    // Should be in English by default
    await expect(page.locator('text=Log In')).toBeVisible();
    await expect(page.locator('text=Email')).toBeVisible();
    await expect(page.locator('text=Password')).toBeVisible();

    // Switch to Chinese
    const languageSelector = page.locator('[data-testid="language-selector"]');
    await languageSelector.click();
    await page.locator('text=简体中文').click();

    // Should translate form
    await expect(page.locator('text=登录')).toBeVisible();
    await expect(page.locator('text=邮箱')).toBeVisible();
    await expect(page.locator('text=密码')).toBeVisible();

    // Test form validation in Chinese
    const emailInput = page.locator('input[type="email"]');
    const submitButton = page.locator('button:has-text("登录")');

    await submitButton.click();

    // Should show Chinese validation error
    await expect(page.locator('text=此字段为必填项')).toBeVisible();
  });

  test('should maintain functionality after language switch', async ({ page }) => {
    // Test in English first
    const chatInput = page.locator('[data-testid="chat-input"]');
    await chatInput.fill('Test message');

    const sendButton = page.locator('button:has-text("Send")');
    await expect(sendButton).toBeVisible();

    // Switch language
    const languageSelector = page.locator('[data-testid="language-selector"]');
    await languageSelector.click();
    await page.locator('text=简体中文').click();

    // Should maintain input value and functionality
    await expect(chatInput).toHaveValue('Test message');
    const chineseSendButton = page.locator('button:has-text("发送")');
    await expect(chineseSendButton).toBeVisible();
  });
});

// Electron-specific E2E tests
test.describe('Electron i18n Tests', () => {
  test('should display Chinese menus in Electron', async ({ page }) => {
    // This would run against the Electron app
    // Test menu items, dialogs, etc.

    // Note: This would require specific Electron test setup
    // with appropriate test runner configuration
  });
});
```

## 5. 测试执行计划

### 5.1 测试阶段规划

#### 阶段1: 开发阶段测试 (开发过程中)
**时间**: 开发期间持续进行
**负责人**: 开发工程师
**测试内容**:
- 单元测试编写和执行
- 基础功能验证
- 代码质量检查

**验收标准**:
- [ ] 单元测试覆盖率达到80%以上
- [ ] 所有基础功能正常工作
- [ ] 代码审查通过

#### 阶段2: 集成测试 (功能完成后)
**时间**: 1-2天
**负责人**: 测试工程师 + 开发工程师
**测试内容**:
- 组件集成测试
- 端到端功能测试
- 跨环境兼容性测试

**验收标准**:
- [ ] 所有集成测试用例通过
- [ ] E2E测试覆盖主要用户流程
- [ ] 兼容性测试通过

#### 阶段3: 用户验收测试 (发布前)
**时间**: 2-3天
**负责人**: 产品经理 + 用户测试员
**测试内容**:
- 真实用户场景测试
- 用户体验评估
- 性能和稳定性测试

**验收标准**:
- [ ] 用户反馈积极
- [ ] 无重大bug
- [ ] 性能指标达标

#### 阶段4: 回归测试 (发布后)
**时间**: 每次版本更新
**负责人**: 自动化测试 + 人工验证
**测试内容**:
- 回归测试用例执行
- 新功能影响评估
- 性能监控

**验收标准**:
- [ ] 回归测试100%通过
- [ ] 新功能不影响现有功能
- [ ] 性能指标稳定

### 5.2 测试执行清单

#### 功能测试清单
```markdown
## Web端功能测试
- [ ] 页面自动语言检测
- [ ] 语言选择器功能
- [ ] 语言切换响应
- [ ] 语言偏好保存
- [ ] 所有页面翻译完整性
- [ ] 导航菜单翻译
- [ ] 表单和验证翻译
- [ ] 错误消息翻译
- [ ] 成功提示翻译

## Electron端功能测试
- [ ] 系统语言检测
- [ ] 应用菜单翻译
- [ ] 系统对话框翻译
- [ ] 通知消息翻译
- [ ] 与Web端同步切换
- [ ] 平台特定功能测试

## 共享组件测试
- [ ] 所有共享组件翻译
- [ ] 参数插值功能
- [ ] 回退机制测试
- [ ] 类型安全验证
- [ ] 性能影响评估
```

#### 兼容性测试清单
```markdown
## 浏览器兼容性
- [ ] Chrome 最新版本
- [ ] Firefox 最新版本
- [ ] Safari 最新版本
- [ ] Edge 最新版本
- [ ] 移动端 Chrome
- [ ] 移动端 Safari

## 操作系统兼容性
- [ ] Windows 10/11
- [ ] macOS 10.14+
- [ ] Ubuntu 18.04+
- [ ] 其他主流Linux发行版

## 设备兼容性
- [ ] 桌面端 (1920x1080)
- [ ] 笔记本 (1366x768)
- [ ] 平板端 (768x1024)
- [ ] 手机端 (375x667)
```

## 6. 测试工具和环境

### 6.1 测试工具清单

#### 自动化测试工具
```json
{
  "unitTesting": {
    "framework": "Jest",
    "rendering": "@testing-library/react",
    "mocking": "jest.mock",
    "coverage": "jest --coverage"
  },
  "e2eTesting": {
    "framework": "Playwright",
    "browsers": ["chromium", "firefox", "webkit"],
    "reporting": "@playwright/test",
    "fixtures": "custom test fixtures"
  },
  "visualTesting": {
    "tool": "Playwright screenshots",
    "comparison": "pixel comparison",
    "baseline": "reference images"
  },
  "performanceTesting": {
    "tools": ["Lighthouse", "WebPageTest"],
    "metrics": ["FCP", "LCP", "TTI", "CLS"],
    "monitoring": "custom performance scripts"
  }
}
```

#### 测试数据管理
```typescript
// tests/fixtures/i18n-fixtures.ts
export const i18nFixtures = {
  languages: {
    en: 'English',
    'zh-CN': '简体中文',
  },

  testPages: [
    {
      name: 'Dashboard',
      path: '/',
      translations: {
        en: ['What would you like to do today?', 'Describe what you need help with...'],
        'zh-CN': ['今天想做什么？', '描述你需要帮助的事项...'],
      },
    },
    {
      name: 'Login',
      path: '/login',
      translations: {
        en: ['Log In', 'Email', 'Password'],
        'zh-CN': ['登录', '邮箱', '密码'],
      },
    },
  ],

  testUsers: [
    {
      id: 'test-user-en',
      preferredLanguage: 'en',
      expectedContent: 'What would you like to do today?',
    },
    {
      id: 'test-user-zh',
      preferredLanguage: 'zh-CN',
      expectedContent: '今天想做什么？',
    },
  ],
};
```

### 6.2 测试环境配置

#### Jest配置 (jest.config.js)
```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{ts,tsx}',
    '!src/**/__tests__/**',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{ts,tsx}',
    '<rootDir>/tests/**/*.{ts,tsx}',
  ],
};
```

#### Playwright配置 (playwright.config.ts)
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

## 7. 性能基准和监控

### 7.1 性能指标基准

#### 启动性能基准
```typescript
// tests/performance/performance-benchmarks.ts
export const performanceBenchmarks = {
  webApp: {
    firstContentfulPaint: 1500, // ms
    largestContentfulPaint: 2500, // ms
    timeToInteractive: 3000, // ms
    cumulativeLayoutShift: 0.1,
  },

  electronApp: {
    startupTime: 5000, // ms
    windowLoadTime: 3000, // ms
    menuLoadTime: 500, // ms
  },

  languageSwitch: {
    responseTime: 300, // ms
    renderTime: 200, // ms
    stateUpdateTime: 50, // ms
  },

  memoryUsage: {
    baselineIncrease: 10, // MB
    translationCacheSize: 2, // MB
    maxMemoryUsage: 200, // MB
  },
};
```

#### 性能测试脚本
```typescript
// tests/performance/language-switch-performance.test.ts
import { test, expect } from '@playwright/test';
import { performanceBenchmarks } from './performance-benchmarks';

test.describe('Language Switch Performance', () => {
  test('should meet performance benchmarks for language switching', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Measure language switch performance
    const startTime = Date.now();

    await page.click('[data-testid="language-selector"]');
    await page.click('text=简体中文');

    // Wait for language switch to complete
    await page.waitForSelector('text=今天想做什么？');

    const endTime = Date.now();
    const switchTime = endTime - startTime;

    // Should complete within benchmark
    expect(switchTime).toBeLessThan(performanceBenchmarks.languageSwitch.responseTime);

    // Check memory usage (if available)
    const memoryUsage = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0;
    });

    console.log(`Language switch time: ${switchTime}ms`);
    console.log(`Memory usage: ${(memoryUsage / 1024 / 1024).toFixed(2)}MB`);
  });
});
```

### 7.2 持续监控配置

#### 性能监控脚本
```typescript
// scripts/monitor-i18n-performance.js
const fs = require('fs');
const path = require('path');

class I18nPerformanceMonitor {
  constructor() {
    this.results = [];
    this.benchmarks = {
      languageSwitchTime: 300,
      translationLoadTime: 100,
      memoryIncrease: 10, // MB
    };
  }

  async measureLanguageSwitch(page) {
    const startTime = Date.now();

    await page.click('[data-testid="language-selector"]');
    await page.click('text=简体中文');
    await page.waitForSelector('text=今天想做什么？');

    const endTime = Date.now();
    return endTime - startTime;
  }

  async measureTranslationLoad(page) {
    const startTime = Date.now();

    await page.evaluate(() => {
      return new Promise((resolve) => {
        // Trigger language change
        window.dispatchEvent(new CustomEvent('language-change', {
          detail: { language: 'zh-CN' }
        }));

        // Wait for translations to load
        setTimeout(resolve, 100);
      });
    });

    const endTime = Date.now();
    return endTime - startTime;
  }

  async measureMemoryUsage(page) {
    const memoryUsage = await page.evaluate(() => {
      if (performance.memory) {
        return {
          used: performance.memory.usedJSHeapSize,
          total: performance.memory.totalJSHeapSize,
          limit: performance.memory.jsHeapSizeLimit,
        };
      }
      return null;
    });

    return memoryUsage;
  }

  async runTests(page) {
    console.log('Starting i18n performance tests...');

    // Test language switch performance
    const switchTime = await this.measureLanguageSwitch(page);
    console.log(`Language switch time: ${switchTime}ms`);

    // Test translation load performance
    const loadTime = await this.measureTranslationLoad(page);
    console.log(`Translation load time: ${loadTime}ms`);

    // Test memory usage
    const memoryUsage = await this.measureMemoryUsage(page);
    if (memoryUsage) {
      console.log(`Memory usage: ${(memoryUsage.used / 1024 / 1024).toFixed(2)}MB`);
    }

    // Save results
    const result = {
      timestamp: new Date().toISOString(),
      languageSwitchTime: switchTime,
      translationLoadTime: loadTime,
      memoryUsage,
    };

    this.results.push(result);
    this.saveResults();

    return result;
  }

  saveResults() {
    const resultsPath = path.join(__dirname, '../performance-results.json');
    fs.writeFileSync(resultsPath, JSON.stringify(this.results, null, 2));
  }

  generateReport() {
    if (this.results.length === 0) {
      return 'No performance data available';
    }

    const avgSwitchTime = this.results.reduce((sum, r) => sum + r.languageSwitchTime, 0) / this.results.length;
    const avgLoadTime = this.results.reduce((sum, r) => sum + r.translationLoadTime, 0) / this.results.length;

    return `
Performance Report:
- Average Language Switch Time: ${avgSwitchTime.toFixed(2)}ms (Target: ${this.benchmarks.languageSwitchTime}ms)
- Average Translation Load Time: ${avgLoadTime.toFixed(2)}ms (Target: ${this.benchmarks.translationLoadTime}ms)
- Total Tests Run: ${this.results.length}
- Last Test: ${this.results[this.results.length - 1].timestamp}
    `.trim();
  }
}

module.exports = I18nPerformanceMonitor;
```

## 8. 问题跟踪和报告

### 8.1 问题分类标准

#### Bug严重性分级
```markdown
## 严重性分级
- **Critical (P0)**: 应用崩溃、安全漏洞、数据丢失
- **High (P1)**: 核心功能不可用、严重显示问题
- **Medium (P2)**: 部分功能异常、用户体验影响
- **Low (P3)**: 轻微显示问题、优化建议
- **Trivial (P4)**: 语法错误、拼写问题
```

#### 问题模板
```markdown
## Bug Report Template

**标题**: [i18n] 语言切换后部分文本未翻译

**复现步骤**:
1. 打开应用
2. 点击语言选择器
3. 选择"简体中文"
4. 查看仪表板页面

**期望结果**:
所有文本都应该显示为中文

**实际结果**:
部分按钮仍显示英文文本

**环境信息**:
- 操作系统: Windows 11
- 浏览器: Chrome 120
- 应用版本: v1.0.0

**截图**:
[附上问题截图]

**附加信息**:
[其他相关信息]
```

### 8.2 测试报告模板

#### 日常测试报告
```markdown
# i18n功能测试日报

**日期**: 2024-01-15
**测试人员**: [姓名]
**测试环境**: 开发环境

## 测试执行情况
- 总测试用例: 45
- 通过: 42
- 失败: 2
- 阻塞: 1

## 发现的问题
1. [P2] 语言切换后侧边栏部分菜单未翻译
2. [P3] 表单验证消息显示异常
3. [P1] Electron菜单翻译不完整 (阻塞)

## 修复状态
- 已修复: 1
- 待修复: 2
- 验证中: 0

## 风险评估
- 高风险: Electron菜单问题可能影响发布
- 中风险: 翻译不完整影响用户体验

## 下一步计划
1. 优先修复Electron菜单翻译问题
2. 完善表单验证消息翻译
3. 补充遗漏的菜单项翻译
```

#### 发布测试报告
```markdown
# i18n功能发布测试报告

**版本**: v1.0.0
**测试周期**: 2024-01-10 ~ 2024-01-15
**测试负责人**: [姓名]

## 测试概述
本次测试主要验证Kortix应用的中英文双语功能，包括Web端和Electron端的国际化支持。

## 测试范围
- ✅ Web端i18n功能
- ✅ Electron端i18n功能
- ✅ 共享组件翻译
- ✅ 性能影响评估
- ✅ 兼容性测试
- ❌ 压力测试 (待执行)

## 测试结果汇总
- 测试用例总数: 156
- 通过率: 96.8% (151/156)
- 发现Bug: 8个
- 严重Bug: 1个
- 已修复Bug: 6个

## 质量评估
### 功能完整性: ⭐⭐⭐⭐⭐
所有核心功能正常工作，翻译覆盖率100%

### 性能表现: ⭐⭐⭐⭐
启动时间增加<10%，语言切换响应<300ms

### 兼容性: ⭐⭐⭐⭐⭐
支持所有主流浏览器和操作系统

### 用户体验: ⭐⭐⭐⭐
语言切换流畅，翻译质量良好

## 风险评估
- 发布风险: 低
- 技术风险: 无重大技术债务
- 维护风险: 需要建立翻译更新流程

## 建议和后续计划
1. 建立翻译质量检查流程
2. 添加翻译管理工具
3. 准备多语言扩展计划
4. 制定用户反馈收集机制

## 发布建议
✅ **建议发布**
当前版本质量良好，可按计划发布。
```

## 9. 成功标准

### 9.1 功能验收标准

#### 核心功能标准
- [ ] **语言自动检测**: 应用能正确检测用户语言偏好
- [ ] **语言切换**: 用户可以流畅切换中英文界面
- [ ] **翻译完整性**: 100%的界面文本都有对应的中文翻译
- [ ] **功能完整性**: 语言切换不影响任何现有功能
- [ ] **状态持久化**: 语言偏好在应用重启后保持

#### 用户体验标准
- [ ] **响应速度**: 语言切换响应时间<300ms
- [ ] **视觉一致性**: 中文文本显示美观，无布局问题
- [ ] **交互一致性**: 所有交互元素在不同语言下行为一致
- [ ] **错误处理**: 翻译缺失时有优雅的回退机制

### 9.2 技术质量标准

#### 代码质量标准
- [ ] **测试覆盖率**: 单元测试覆盖率≥80%
- [ ] **类型安全**: 无TypeScript类型错误
- [ ] **代码规范**: 通过ESLint检查
- [ ] **性能基准**: 满足所有性能指标要求

#### 兼容性标准
- [ ] **浏览器兼容**: 支持主流浏览器最新版本
- [ ] **设备兼容**: 支持桌面端和移动端设备
- [ ] **平台兼容**: 支持Windows、macOS、Linux

### 9.3 发布标准

#### 发布前检查清单
```markdown
## 功能检查
- [ ] 所有测试用例通过
- [ ] 性能指标达标
- [ ] 兼容性测试通过
- [ ] 安全性检查通过

## 文档检查
- [ ] 用户文档更新
- [ ] 开发文档完整
- [ ] 部署文档更新
- [ ] 维护文档准备

## 发布准备
- [ ] 版本号更新
- [ ] 变更日志准备
- [ ] 发布说明编写
- [ ] 回滚计划准备
```

## 10. 持续改进计划

### 10.1 短期改进 (1-3个月)

#### 翻译质量提升
- 建立翻译审核流程
- 收集用户翻译反馈
- 优化翻译文本表达
- 补充遗漏的翻译内容

#### 测试自动化增强
- 增加E2E测试覆盖率
- 实现视觉回归测试
- 添加性能监控自动化
- 建立持续集成流程

### 10.2 中期改进 (3-6个月)

#### 工具和流程优化
- 开发翻译管理工具
- 实现协作翻译流程
- 建立翻译质量评估体系
- 优化构建和部署流程

#### 功能扩展
- 支持繁体中文翻译
- 实现动态语言包加载
- 添加语言偏好云端同步
- 支持区域化设置

### 10.3 长期规划 (6个月以上)

#### 多语言支持
- 支持日语、韩语等亚洲语言
- 实现RTL语言支持
- 添加复数形式处理
- 支持地区化差异

#### 智能化翻译
- 集成机器翻译API
- 实现翻译记忆库
- 添加翻译质量检查
- 支持A/B测试

---

**文档版本**: v1.0
**最后更新**: 2024-01-15
**负责人**: [测试团队]
**审核人**: [技术负责人]

这份测试验证方案为Kortix应用的i18n功能提供了全面的测试框架，确保中文化功能的质量和可靠性。通过系统性的测试方法和持续改进计划，可以为用户提供优秀的多语言体验。