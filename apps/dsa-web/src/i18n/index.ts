import type { Language } from '../stores/themeStore';
import { zh } from './zh';
import { en } from './en';

export type TranslationKeys = typeof zh;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const translations: Record<Language, TranslationKeys> = { zh, en: en as any };

export function t(lang: Language, key: string): string {
  const parts = key.split('.');
  let current: unknown = translations[lang];
  for (const part of parts) {
    if (current && typeof current === 'object' && part in current) {
      current = (current as Record<string, unknown>)[part];
    } else {
      return key;
    }
  }
  return typeof current === 'string' ? current : key;
}

export { zh, en };
