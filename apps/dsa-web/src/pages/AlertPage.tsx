import type React from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../hooks/useTranslation';

interface AlertRule {
  id: string;
  stockCode: string;
  type: 'price_above' | 'price_below' | 'change_above' | 'change_below';
  threshold: string;
  enabled: boolean;
}

const ALERT_TYPE_LABELS: Record<AlertRule['type'], string> = {
  price_above: '价格高于',
  price_below: '价格低于',
  change_above: '涨幅超过',
  change_below: '跌幅超过',
};

let nextId = 1;

const AlertPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [stockCode, setStockCode] = useState('');
  const [alertType, setAlertType] = useState<AlertRule['type']>('price_above');
  const [threshold, setThreshold] = useState('');

  const handleAdd = () => {
    if (!stockCode.trim() || !threshold.trim()) return;
    const rule: AlertRule = {
      id: `alert-${nextId++}`,
      stockCode: stockCode.toUpperCase(),
      type: alertType,
      threshold,
      enabled: true,
    };
    setRules((prev) => [...prev, rule]);
    setStockCode('');
    setThreshold('');
  };

  const handleToggle = (id: string) => {
    setRules((prev) =>
      prev.map((r) => (r.id === id ? { ...r, enabled: !r.enabled } : r)),
    );
  };

  const handleRemove = (id: string) => {
    setRules((prev) => prev.filter((r) => r.id !== id));
  };

  return (
    <div className="page-container">
      <header className="page-header">
        <button className="page-back-btn" onClick={() => navigate('/')}>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          <span>{t('actions.back')}</span>
        </button>
        <h1 className="page-title">{t('home.toolAlert')}</h1>
      </header>

      {/* Add rule form */}
      <div className="tool-page-card">
        <h3 className="tool-page-card-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          添加预警规则
        </h3>
        <div className="alert-form">
          <input
            type="text"
            value={stockCode}
            onChange={(e) => setStockCode(e.target.value.toUpperCase())}
            placeholder="股票代码，如 600519"
            className="alert-form-input"
          />
          <select
            className="tool-page-select"
            value={alertType}
            onChange={(e) => setAlertType(e.target.value as AlertRule['type'])}
            title="预警类型"
          >
            {Object.entries(ALERT_TYPE_LABELS).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>
          <input
            type="text"
            value={threshold}
            onChange={(e) => setThreshold(e.target.value)}
            placeholder={alertType.includes('change') ? '百分比，如 5' : '价格，如 1800'}
            className="alert-form-input"
          />
          <button
            onClick={handleAdd}
            disabled={!stockCode.trim() || !threshold.trim()}
            className="analysis-submit-btn"
          >
            添加规则
          </button>
        </div>
      </div>

      {/* Rules list */}
      {rules.length > 0 && (
        <div className="tool-page-card">
          <h3 className="tool-page-card-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            预警规则列表（{rules.length}）
          </h3>
          <div className="alert-rules-list">
            {rules.map((rule) => (
              <div key={rule.id} className={`alert-rule-item ${rule.enabled ? '' : 'alert-rule-disabled'}`}>
                <div className="alert-rule-info">
                  <span className="alert-rule-code">{rule.stockCode}</span>
                  <span className="alert-rule-condition">
                    {ALERT_TYPE_LABELS[rule.type]}
                    <strong>
                      {rule.type.includes('change') ? `${rule.threshold}%` : `¥${rule.threshold}`}
                    </strong>
                  </span>
                </div>
                <div className="alert-rule-actions">
                  <button
                    className={`alert-toggle-btn ${rule.enabled ? 'alert-toggle-on' : 'alert-toggle-off'}`}
                    onClick={() => handleToggle(rule.id)}
                    title={rule.enabled ? '停用' : '启用'}
                  >
                    {rule.enabled ? '已启用' : '已停用'}
                  </button>
                  <button className="alert-remove-btn" onClick={() => handleRemove(rule.id)} title="删除">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Info banner */}
      <div className="tool-page-card">
        <h3 className="tool-page-card-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          关于预警通知
        </h3>
        <p className="tool-page-card-body">
          预警规则创建后将在本地保存。如需推送通知到微信、钉钉或其他渠道，请前往
          <button className="tool-page-inline-link" onClick={() => navigate('/settings')}>系统设置 → 通知渠道</button>
          配置 Webhook 和推送令牌。
        </p>
      </div>

      {rules.length === 0 && (
        <div className="page-empty">
          <div className="page-empty-icon">
            <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </div>
          <h3>智能预警中心</h3>
          <p>设置价格预警和涨跌幅提醒，实时监控自选股动态</p>
        </div>
      )}
    </div>
  );
};

export default AlertPage;
