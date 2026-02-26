import { useCallback } from 'react';
import { useThemeStore } from '../stores/themeStore';
import { t } from '../i18n';

export function useTranslation() {
  const language = useThemeStore((s) => s.language);
  const translate = useCallback((key: string) => t(language, key), [language]);
  return { t: translate, language };
}
