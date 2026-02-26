import type React from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../hooks/useTranslation';

const MarketReviewPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');

  const tabs = [
    { key: 'overview', label: t('market.overview'), icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
    { key: 'sectors', label: t('market.sectors'), icon: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z' },
    { key: 'northbound', label: t('market.northbound'), icon: 'M7 11l5-5m0 0l5 5m-5-5v12' },
    { key: 'indices', label: t('market.indices'), icon: 'M7 12l3-3 3 3 4-4' },
  ];

  const indices = [
    { label: '上证指数', code: '000001.SH', value: '3,285.07', change: '+1.24%', up: true },
    { label: '深证成指', code: '399001.SZ', value: '10,156.32', change: '+0.87%', up: true },
    { label: '创业板指', code: '399006.SZ', value: '2,045.18', change: '-0.32%', up: false },
    { label: '科创50', code: '000688.SH', value: '986.54', change: '+2.15%', up: true },
    { label: '北向资金', code: 'NORTH', value: '+52.3亿', change: '净流入', up: true },
    { label: '沪深300', code: '000300.SH', value: '3,842.16', change: '+0.95%', up: true },
  ];

  const sectors = [
    { label: '半导体', change: '+3.21%', up: true, heat: 'hot' },
    { label: '新能源汽车', change: '+2.45%', up: true, heat: 'hot' },
    { label: '人工智能', change: '+1.87%', up: true, heat: 'warm' },
    { label: '医药生物', change: '-0.56%', up: false, heat: 'cold' },
    { label: '白酒', change: '+0.32%', up: true, heat: 'cold' },
    { label: '银行', change: '-0.18%', up: false, heat: 'cold' },
    { label: '光伏', change: '+1.12%', up: true, heat: 'warm' },
    { label: '军工', change: '+0.78%', up: true, heat: 'warm' },
  ];

  return (
    <div className="page-container">
      <header className="page-header">
        <button className="page-back-btn" onClick={() => navigate('/')}>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7"/>
          </svg>
          <span>{t('actions.back')}</span>
        </button>
        <h1 className="page-title">{t('market.title')}</h1>
        <span className="page-badge-coming-soon">{t('common.comingSoon')}</span>
      </header>

      {/* Tabs */}
      <div className="market-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            className={`market-tab ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d={tab.icon}/>
            </svg>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Overview tab */}
      {activeTab === 'overview' && (
        <>
          <section className="market-section">
            <h2 className="market-section-title">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
              </svg>
              主要指数
            </h2>
            <div className="market-index-grid">
              {indices.map((idx) => (
                <div key={idx.code} className={`market-index-card ${idx.up ? 'up' : 'down'}`}>
                  <div className="market-index-header">
                    <span className="market-index-label">{idx.label}</span>
                    <span className="market-index-code">{idx.code}</span>
                  </div>
                  <span className="market-index-value">{idx.value}</span>
                  <span className="market-index-change">{idx.change}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="market-section">
            <h2 className="market-section-title">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6z"/>
              </svg>
              板块热度
            </h2>
            <div className="market-sector-grid">
              {sectors.map((s) => (
                <div key={s.label} className={`market-sector-card ${s.up ? 'up' : 'down'}`}>
                  <span className="market-sector-label">{s.label}</span>
                  <span className="market-sector-change">{s.change}</span>
                  <span className={`market-sector-heat ${s.heat}`}>
                    {s.heat === 'hot' ? '🔥' : s.heat === 'warm' ? '📈' : '📉'}
                  </span>
                </div>
              ))}
            </div>
          </section>
        </>
      )}

      {/* Other tabs — coming soon */}
      {activeTab !== 'overview' && (
        <div className="market-coming-soon">
          <div className="market-coming-soon-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </div>
          <h3>功能开发中</h3>
          <p>{tabs.find(t => t.key === activeTab)?.label} 模块即将上线，敬请期待</p>
        </div>
      )}

      {/* Disclaimer */}
      <div className="market-disclaimer">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <span>数据为模拟展示，实时行情功能开发中。接入后将自动更新。</span>
      </div>
    </div>
  );
};

export default MarketReviewPage;
