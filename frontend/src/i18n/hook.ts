import { useI18n } from './context';

export { useI18n } from './context';
export type { I18nContextType, Language, TranslationParams } from './types';
export { detectLanguage, translations, supportedLanguages, getLanguageDisplayName, isSupportedLanguage } from './index';

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

// 专门用于表单验证的Hook
export const useFormTranslation = () => {
  const { t } = useI18n();

  return {
    required: (field?: string) => t('forms.required', { field }),
    invalidEmail: () => t('forms.invalidEmail'),
    passwordTooShort: (minLength?: number) => t('forms.passwordTooShort', { minLength }),
    passwordsNotMatch: () => t('forms.passwordsNotMatch'),
    genericError: () => t('forms.genericError')
  };
};

// 用于错误消息的Hook
export const useErrorTranslation = () => {
  const { t } = useI18n();

  return {
    networkError: () => t('errors.networkError'),
    serverError: () => t('errors.serverError'),
    unauthorized: () => t('errors.unauthorized'),
    forbidden: () => t('errors.forbidden'),
    notFound: () => t('errors.notFound'),
    somethingWentWrong: () => t('errors.somethingWentWrong'),
    customError: (message: string) => {
      // 尝试翻译，如果找不到则返回原始消息
      const translated = t(`errors.${message}`);
      return translated !== `errors.${message}` ? translated : message;
    }
  };
};