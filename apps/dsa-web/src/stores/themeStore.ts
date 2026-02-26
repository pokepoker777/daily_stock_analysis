import { create } from 'zustand';

export type ThemeMode = 'light' | 'dark';
export type Language = 'zh' | 'en';

interface ThemeState {
  theme: ThemeMode;
  language: Language;
  sidebarCollapsed: boolean;
  setTheme: (theme: ThemeMode) => void;
  toggleTheme: () => void;
  setLanguage: (lang: Language) => void;
  toggleLanguage: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
}

const getInitialTheme = (): ThemeMode => {
  const stored = localStorage.getItem('dsa-theme');
  if (stored === 'light' || stored === 'dark') return stored;
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

const getInitialLanguage = (): Language => {
  const stored = localStorage.getItem('dsa-language');
  if (stored === 'zh' || stored === 'en') return stored;
  return navigator.language.startsWith('zh') ? 'zh' : 'en';
};

export const useThemeStore = create<ThemeState>((set, get) => ({
  theme: getInitialTheme(),
  language: getInitialLanguage(),
  sidebarCollapsed: false,

  setTheme: (theme) => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('dsa-theme', theme);
    set({ theme });
  },

  toggleTheme: () => {
    const next = get().theme === 'light' ? 'dark' : 'light';
    get().setTheme(next);
  },

  setLanguage: (language) => {
    document.documentElement.setAttribute('lang', language);
    localStorage.setItem('dsa-language', language);
    set({ language });
  },

  toggleLanguage: () => {
    const next = get().language === 'zh' ? 'en' : 'zh';
    get().setLanguage(next);
  },

  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
}));
