import en from '../../messages/en.json';
import zhCN from '../../messages/zh-CN.json';
import electron from '../../messages/electron.json';
import type { Language, TranslationResources, TranslationParams } from './types';

// 合并翻译资源
export const translations = {
  en: en as TranslationResources,
  'zh-CN': {
    ...zhCN as TranslationResources,
    // 合并Electron特有翻译
    electron: electron.zhCN
  }
} as const;

export const defaultLanguage: Language = 'en';
export const supportedLanguages: Language[] = ['en', 'zh-CN'];

// 语言检测逻辑
export const detectLanguage = (): Language => {
  // 服务端环境
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

// 获取语言显示名称
export const getLanguageDisplayName = (language: Language): string => {
  const names = {
    en: 'English',
    'zh-CN': '简体中文'
  };
  return names[language];
};

// 检查是否为支持的语言
export const isSupportedLanguage = (lang: string): lang is Language => {
  return supportedLanguages.includes(lang as Language);
};