import type React from 'react';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSystemConfig } from '../hooks';
import { useTranslation } from '../hooks/useTranslation';
import { useThemeStore } from '../stores/themeStore';
import { SettingsAlert, SettingsField, SettingsLoading } from '../components/settings';
import { getCategoryDescriptionZh, getCategoryTitleZh } from '../utils/systemConfigI18n';

const SettingsPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const theme = useThemeStore((s) => s.theme);
  const language = useThemeStore((s) => s.language);
  const toggleTheme = useThemeStore((s) => s.toggleTheme);
  const toggleLanguage = useThemeStore((s) => s.toggleLanguage);
  const {
    categories,
    itemsByCategory,
    issueByKey,
    activeCategory,
    setActiveCategory,
    hasDirty,
    dirtyCount,
    toast,
    clearToast,
    isLoading,
    isSaving,
    loadError,
    saveError,
    retryAction,
    load,
    retry,
    save,
    setDraftValue,
  } = useSystemConfig();

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!toast) {
      return;
    }

    const timer = window.setTimeout(() => {
      clearToast();
    }, 3200);

    return () => {
      window.clearTimeout(timer);
    };
  }, [clearToast, toast]);

  const activeItems = itemsByCategory[activeCategory] || [];

  return (
    <div className="page-container">
      {/* Page header */}
      <div className="page-header">
        <button className="page-back-btn" onClick={() => navigate('/')}>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7"/>
          </svg>
          <span>{t('actions.back')}</span>
        </button>
        <h1 className="page-title">{t('settings.title')}</h1>
      </div>

      {/* Theme / Language quick toggles */}
      <div className="settings-toggles">
        <div className="settings-toggle-group">
          <span className="settings-toggle-label">{t('settings.theme')}</span>
          <button className={`settings-toggle-btn ${theme === 'light' ? 'active' : ''}`} onClick={() => { if (theme !== 'light') toggleTheme(); }}>
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
            {t('settings.themeLight')}
          </button>
          <button className={`settings-toggle-btn ${theme === 'dark' ? 'active' : ''}`} onClick={() => { if (theme !== 'dark') toggleTheme(); }}>
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>
            {t('settings.themeDark')}
          </button>
        </div>
        <div className="settings-toggle-group">
          <span className="settings-toggle-label">{t('settings.language')}</span>
          <button className={`settings-toggle-btn ${language === 'zh' ? 'active' : ''}`} onClick={() => { if (language !== 'zh') toggleLanguage(); }}>
            {t('settings.languageZh')}
          </button>
          <button className={`settings-toggle-btn ${language === 'en' ? 'active' : ''}`} onClick={() => { if (language !== 'en') toggleLanguage(); }}>
            {t('settings.languageEn')}
          </button>
        </div>
      </div>

      {/* System config */}
      <header className="settings-config-header">
        <div className="settings-config-header-inner">
          <div>
            <h2 className="settings-config-title">{t('settings.apiConfig')}</h2>
          </div>
          <div className="settings-config-actions">
            <button type="button" className="page-back-btn" onClick={() => void load()} disabled={isLoading || isSaving}>
              {t('actions.reset')}
            </button>
            <button
              type="button"
              className="analysis-submit-btn"
              onClick={() => void save()}
              disabled={!hasDirty || isSaving || isLoading}
            >
              {isSaving ? t('common.loading') : `${t('actions.save')}${dirtyCount ? ` (${dirtyCount})` : ''}`}
            </button>
          </div>
        </div>

        {saveError ? (
          <SettingsAlert
            className="mt-3"
            title="保存失败"
            message={saveError}
            actionLabel={retryAction === 'save' ? '重试保存' : undefined}
            onAction={retryAction === 'save' ? () => void retry() : undefined}
          />
        ) : null}
      </header>

      {loadError ? (
        <SettingsAlert
          title="加载设置失败"
          message={loadError}
          actionLabel={retryAction === 'load' ? '重试加载' : '重新加载'}
          onAction={() => void retry()}
          className="mb-4"
        />
      ) : null}

      {isLoading ? (
        <SettingsLoading />
      ) : (
        <div className="settings-grid">
          <aside className="settings-categories">
            <p className="settings-categories-label">配置分类</p>
            <div className="settings-categories-list">
              {categories.map((category) => {
                const isActive = category.category === activeCategory;
                const count = (itemsByCategory[category.category] || []).length;
                const title = getCategoryTitleZh(category.category, category.title);
                const description = getCategoryDescriptionZh(category.category, category.description);

                return (
                  <button
                    key={category.category}
                    type="button"
                    className={`settings-category-btn ${isActive ? 'active' : ''}`}
                    onClick={() => setActiveCategory(category.category)}
                  >
                    <span className="settings-category-header">
                      {title}
                      <span className="settings-category-count">{count}</span>
                    </span>
                    {description ? <span className="settings-category-desc">{description}</span> : null}
                  </button>
                );
              })}
            </div>
          </aside>

          <section className="settings-fields">
            {activeItems.length ? (
              activeItems.map((item) => (
                <SettingsField
                  key={item.key}
                  item={item}
                  value={item.value}
                  disabled={isSaving}
                  onChange={setDraftValue}
                  issues={issueByKey[item.key] || []}
                />
              ))
            ) : (
              <div className="settings-empty-category">
                当前分类下暂无配置项。
              </div>
            )}
          </section>
        </div>
      )}

      {toast ? (
        <div className="settings-toast">
          <SettingsAlert
            title={toast.type === 'success' ? '操作成功' : '操作失败'}
            message={toast.message}
            variant={toast.type === 'success' ? 'success' : 'error'}
          />
        </div>
      ) : null}
    </div>
  );
};

export default SettingsPage;
