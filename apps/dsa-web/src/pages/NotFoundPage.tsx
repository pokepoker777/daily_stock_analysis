import type React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../hooks/useTranslation';

const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <div className="not-found-page">
      <h1>404</h1>
      <p>{t('common.error')}</p>
      <button className="page-back-btn" onClick={() => navigate('/')}>
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7"/>
        </svg>
        <span>{t('actions.back')}</span>
      </button>
    </div>
  );
};

export default NotFoundPage;
