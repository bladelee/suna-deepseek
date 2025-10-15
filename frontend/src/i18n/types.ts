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

declare global {
  interface Window {
    electronAPI?: any;
  }
}