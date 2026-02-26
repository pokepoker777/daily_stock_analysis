import type React from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../hooks/useTranslation';
import { validateStockCode } from '../utils/validation';

const NewHomePage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [stockCode, setStockCode] = useState('');
  const [inputError, setInputError] = useState<string>();
  const [activeCategory, setActiveCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const handleAnalyze = () => {
    const { valid, message, normalized } = validateStockCode(stockCode);
    if (!valid) { setInputError(message); return; }
    setInputError(undefined);
    navigate(`/analysis?code=${encodeURIComponent(normalized)}`);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && stockCode.trim()) handleAnalyze();
  };

  const featureCards = [
    {
      key: 'analysis', route: '/analysis', gradient: 'purple',
      icon: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6',
      title: t('features.stockAnalysis'),
      desc: t('features.stockAnalysisDesc'),
      action: t('home.startAnalysis'),
    },
    {
      key: 'market', route: '/market', gradient: 'blue',
      icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
      title: t('features.marketReview'),
      desc: t('features.marketReviewDesc'),
      action: t('home.viewReview'),
    },
    {
      key: 'backtest', route: '/backtest', gradient: 'orange',
      icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
      title: t('features.aiBacktest'),
      desc: t('features.aiBacktestDesc'),
      action: t('home.viewBacktest'),
    },
  ];

  const quickLinks = [
    { key: 'portfolio', route: '/portfolio', gradientClass: 'gradient-pink', title: t('features.portfolioRisk'), desc: t('features.portfolioRiskDesc'), icon: 'M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z' },
    { key: 'data', route: '/discover', gradientClass: 'gradient-cyan', title: t('features.dataCenter'), desc: t('features.dataCenterDesc'), icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10' },
    { key: 'settings', route: '/settings', gradientClass: 'gradient-blue', title: t('nav.settings'), desc: t('settings.apiConfig'), icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' },
  ];

  const categories = [
    { key: 'all', label: t('home.allCategories') },
    { key: 'analysis', label: t('home.catAnalysis') },
    { key: 'data', label: t('home.catData') },
    { key: 'risk', label: t('home.catRisk') },
    { key: 'research', label: t('home.catResearch') },
  ];

  const tools = [
    { key: 'smart-report', cat: 'analysis', route: '/analysis', gradientClass: 'gradient-purple', title: t('home.toolSmartReport'), desc: t('home.toolSmartReportDesc'), users: '2.6万+', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
    { key: 'technicals', cat: 'analysis', route: '/tools/technicals', gradientClass: 'gradient-blue', title: t('home.toolTechnicals'), desc: t('home.toolTechnicalsDesc'), users: '1.8万+', icon: 'M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z' },
    { key: 'sentiment', cat: 'data', route: '/tools/sentiment', gradientClass: 'gradient-green', title: t('home.toolSentiment'), desc: t('home.toolSentimentDesc'), users: '1.2万+', icon: 'M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z' },
    { key: 'screener', cat: 'data', route: '/tools/screener', gradientClass: 'gradient-orange', title: t('home.toolScreener'), desc: t('home.toolScreenerDesc'), users: '9800+', icon: 'M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z' },
    { key: 'compare', cat: 'analysis', route: '/tools/compare', gradientClass: 'gradient-cyan', title: t('home.toolCompare'), desc: t('home.toolCompareDesc'), users: '7500+', icon: 'M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2' },
    { key: 'alert', cat: 'risk', route: '/tools/alert', gradientClass: 'gradient-pink', title: t('home.toolAlert'), desc: t('home.toolAlertDesc'), users: '5200+', icon: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9' },
  ];

  const filteredTools = tools.filter(t => {
    const matchCat = activeCategory === 'all' || t.cat === activeCategory;
    const matchSearch = !searchQuery || t.title.toLowerCase().includes(searchQuery.toLowerCase()) || t.desc.toLowerCase().includes(searchQuery.toLowerCase());
    return matchCat && matchSearch;
  });

  return (
    <div className="home-page">
      {/* ===== Hero Banner ===== */}
      <div className="home-hero">
        <div className="home-hero-content">
          <span className="home-hero-tag">{t('home.heroTag')}</span>
          <h1 className="home-hero-title">{t('home.heroTitle')}</h1>
          <p className="home-hero-desc">{t('home.heroDesc')}</p>
          <div className="home-hero-input">
            <input
              type="text"
              value={stockCode}
              onChange={(e) => { setStockCode(e.target.value.toUpperCase()); setInputError(undefined); }}
              onKeyDown={handleKeyDown}
              placeholder={t('app.inputPlaceholder')}
            />
            <button
              className="home-hero-cta"
              disabled={!stockCode.trim()}
              onClick={handleAnalyze}
              title={t('home.startNow')}
            >
              {t('home.startNow')}
            </button>
          </div>
          {inputError && <p className="home-hero-error">{inputError}</p>}
        </div>
        <div className="home-hero-decoration">
          <div className="home-hero-visual" />
        </div>
      </div>

      {/* ===== Feature Cards Row (3 gradient + quick links) ===== */}
      <div className="home-features-row">
        <div className="home-features-main">
          {featureCards.map((card) => (
            <button
              key={card.key}
              className={`home-gradient-card ${card.gradient}`}
              onClick={() => navigate(card.route)}
              title={card.title}
            >
              <div>
                <div className="home-gradient-card-icon">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
                    <path strokeLinecap="round" strokeLinejoin="round" d={card.icon} />
                  </svg>
                </div>
                <h3>{card.title}</h3>
                <p>{card.desc}</p>
              </div>
              <span className="home-gradient-card-action">
                {card.action} →
              </span>
            </button>
          ))}
        </div>

        <div className="home-quick-links">
          {quickLinks.map((link) => (
            <div
              key={link.key}
              className="home-quick-link"
              onClick={() => navigate(link.route)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && navigate(link.route)}
            >
              <div className={`home-quick-link-icon ${link.gradientClass}`}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
                  <path strokeLinecap="round" strokeLinejoin="round" d={link.icon} />
                </svg>
              </div>
              <div>
                <h4>{link.title}</h4>
                <span>{link.desc}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ===== Category Tabs + Search ===== */}
      <div className="home-category-bar">
        <div className="home-category-tabs">
          {categories.map((cat) => (
            <button
              key={cat.key}
              className={`home-category-tab ${activeCategory === cat.key ? 'active' : ''}`}
              onClick={() => setActiveCategory(cat.key)}
            >
              {cat.label}
            </button>
          ))}
        </div>
        <div className="home-search-box">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input type="text" placeholder={t('home.searchTools')} value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
        </div>
      </div>

      {/* ===== Tool Grid ===== */}
      <div className="home-tools-grid">
        {filteredTools.map((tool) => (
          <div
            key={tool.key}
            className="home-tool-card"
            onClick={() => navigate(tool.route)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && navigate(tool.route)}
          >
            <div className={`home-tool-avatar ${tool.gradientClass}`}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d={tool.icon} />
              </svg>
            </div>
            <div className="home-tool-info">
              <h4>{tool.title}</h4>
              <p>{tool.desc}</p>
              <div className="home-tool-meta">
                <span className="home-tool-stat">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                  </svg>
                  {tool.users}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NewHomePage;
