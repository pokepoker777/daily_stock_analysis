import type React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../hooks/useTranslation';

const DataCenterPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const tools = [
    { key: 'indicators', label: '技术指标', desc: 'BOLL / ATR / KDJ / OBV / CCI', icon: 'M7 12l3-3 3 3 4-4', colorClass: 'color-blue', route: '/tools/technicals', status: 'active' as const },
    { key: 'validator', label: '数据校验', desc: '多源一致性检验', icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z', colorClass: 'color-green', route: null, status: 'coming' as const },
    { key: 'metrics', label: '系统监控', desc: 'Prometheus 指标面板', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z', colorClass: 'color-purple', route: null, status: 'coming' as const },
    { key: 'channels', label: '通知渠道', desc: '微信 / 飞书 / Telegram / 邮件', icon: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9', colorClass: 'color-orange', route: '/settings', status: 'active' as const },
    { key: 'ratelimit', label: '限流管理', desc: 'Token Bucket 速率控制', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z', colorClass: 'color-pink', route: '/settings', status: 'active' as const },
    { key: 'circuit', label: '熔断器', desc: '外部服务健康监控', icon: 'M13 10V3L4 14h7v7l9-11h-7z', colorClass: 'color-cyan', route: null, status: 'coming' as const },
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
        <h1 className="page-title">{t('features.dataCenter')}</h1>
      </header>

      <div className="discover-grid">
        {tools.map((tool) => (
          <button
            key={tool.key}
            className={`discover-card ${tool.status === 'coming' ? 'discover-card-disabled' : ''}`}
            onClick={() => tool.route && navigate(tool.route)}
          >
            <div className={`discover-card-icon ${tool.colorClass}`}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d={tool.icon}/>
              </svg>
            </div>
            <div className="discover-card-text">
              <span className="discover-card-label">
                {tool.label}
                {tool.status === 'coming' && <span className="discover-card-badge">开发中</span>}
              </span>
              <span className="discover-card-desc">{tool.desc}</span>
            </div>
            {tool.route && (
              <svg className="discover-card-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7"/>
              </svg>
            )}
          </button>
        ))}
      </div>
    </div>
  );
};

export default DataCenterPage;
