import type React from 'react';
import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useThemeStore } from './stores/themeStore';
import { useTranslation } from './hooks/useTranslation';
import HomePage from './pages/NewHomePage';
import AnalysisPage from './pages/AnalysisPage';
import MarketReviewPage from './pages/MarketReviewPage';
import BacktestPage from './pages/BacktestPage';
import PortfolioRiskPage from './pages/PortfolioRiskPage';
import DataCenterPage from './pages/DataCenterPage';
import SettingsPage from './pages/SettingsPage';
import TechnicalsPage from './pages/TechnicalsPage';
import SentimentPage from './pages/SentimentPage';
import ScreenerPage from './pages/ScreenerPage';
import ComparePage from './pages/ComparePage';
import AlertPage from './pages/AlertPage';
import NotFoundPage from './pages/NotFoundPage';
import './App.css';

/* ================================================================
   Sidebar
   ================================================================ */
const Sidebar: React.FC = () => {
  const { t } = useTranslation();
  const collapsed = useThemeStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useThemeStore((s) => s.toggleSidebar);
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { key: 'home', to: '/', label: t('nav.home'), icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
    { key: 'analysis', to: '/analysis', label: t('nav.analysis'), icon: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6' },
    { key: 'market', to: '/market', label: t('nav.market'), icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
    { key: 'backtest', to: '/backtest', label: t('nav.backtest'), icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4' },
    { key: 'portfolio', to: '/portfolio', label: t('nav.portfolio'), icon: 'M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z' },
    { key: 'data', to: '/discover', label: t('nav.discover'), icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10' },
  ];

  return (
    <aside className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''}`}>
      {/* Logo + collapse toggle */}
      <div className="sidebar-header">
        <NavLink to="/" className="sidebar-logo">
          <svg className="w-6 h-6 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
          </svg>
          {!collapsed && <span className="sidebar-logo-text">{t('app.name')}</span>}
        </NavLink>
        <button onClick={toggleSidebar} className="sidebar-toggle" title="Toggle sidebar">
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            {collapsed
              ? <path strokeLinecap="round" strokeLinejoin="round" d="M13 5l7 7-7 7M5 5l7 7-7 7"/>
              : <path strokeLinecap="round" strokeLinejoin="round" d="M11 19l-7-7 7-7m8 14l-7-7 7-7"/>
            }
          </svg>
        </button>
      </div>

      {/* New analysis button */}
      <button
        className="sidebar-new-btn"
        onClick={() => navigate('/analysis')}
      >
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4"/>
        </svg>
        {!collapsed && <span>{t('app.newChat')}</span>}
      </button>

      {/* Navigation items */}
      <nav className="sidebar-nav">
        {!collapsed && <p className="sidebar-section-label">{t('nav.home')}</p>}
        {navItems.map((item) => {
          const isActive = item.to === '/'
            ? location.pathname === '/'
            : location.pathname.startsWith(item.to);
          return (
            <NavLink
              key={item.key}
              to={item.to}
              className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
              title={item.label}
            >
              <svg className="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d={item.icon}/>
              </svg>
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom: settings + user */}
      <div className="sidebar-footer">
        <NavLink
          to="/settings"
          className={`sidebar-nav-item ${location.pathname === '/settings' ? 'active' : ''}`}
          title={t('nav.settings')}
        >
          <svg className="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
          </svg>
          {!collapsed && <span>{t('nav.settings')}</span>}
        </NavLink>
        <div className="sidebar-user">
          <div className="sidebar-avatar">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
            </svg>
          </div>
          {!collapsed && <span className="sidebar-user-label">{t('app.mySpace')}</span>}
        </div>
      </div>
    </aside>
  );
};

/* ================================================================
   Top Bar
   ================================================================ */
const TopBar: React.FC = () => {
  const { t } = useTranslation();
  const theme = useThemeStore((s) => s.theme);
  const language = useThemeStore((s) => s.language);
  const toggleTheme = useThemeStore((s) => s.toggleTheme);
  const toggleLanguage = useThemeStore((s) => s.toggleLanguage);

  return (
    <header className="topbar">
      <div className="topbar-left">
        <span className="topbar-model-badge">Gemini + DeepSeek</span>
      </div>
      <div className="topbar-right">
        <button className="topbar-btn" onClick={toggleLanguage} title={t('settings.language')}>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9"/>
          </svg>
          <span className="topbar-btn-label">{language === 'zh' ? '中' : 'EN'}</span>
        </button>
        <button className="topbar-btn" onClick={toggleTheme} title={t('settings.theme')}>
          {theme === 'dark' ? (
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/>
            </svg>
          ) : (
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/>
            </svg>
          )}
        </button>
      </div>
    </header>
  );
};

/* ================================================================
   Theme Initializer
   ================================================================ */
const ThemeInit: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const theme = useThemeStore((s) => s.theme);
  const language = useThemeStore((s) => s.language);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('lang', language);
  }, [theme, language]);

  return <>{children}</>;
};

/* ================================================================
   App
   ================================================================ */
const App: React.FC = () => {
  return (
    <ThemeInit>
      <Router>
        <div className="app-layout">
          <Sidebar />
          <div className="app-main">
            <TopBar />
            <main className="app-content">
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/analysis" element={<AnalysisPage />} />
                <Route path="/market" element={<MarketReviewPage />} />
                <Route path="/backtest" element={<BacktestPage />} />
                <Route path="/portfolio" element={<PortfolioRiskPage />} />
                <Route path="/discover" element={<DataCenterPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/tools/technicals" element={<TechnicalsPage />} />
                <Route path="/tools/sentiment" element={<SentimentPage />} />
                <Route path="/tools/screener" element={<ScreenerPage />} />
                <Route path="/tools/compare" element={<ComparePage />} />
                <Route path="/tools/alert" element={<AlertPage />} />
                <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </main>
          </div>
        </div>
      </Router>
    </ThemeInit>
  );
};

export default App;
