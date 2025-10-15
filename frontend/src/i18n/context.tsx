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
    return <div className="flex items-center justify-center h-screen">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
    </div>;
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