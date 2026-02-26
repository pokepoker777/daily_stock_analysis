import type React from 'react';

export const SettingsLoading: React.FC = () => {
  return (
    <div className="settings-loading">
      {Array.from({ length: 6 }).map((_, index) => (
        <div key={index} className="settings-loading-card">
          <div className="settings-loading-line settings-loading-line-short" />
          <div className="settings-loading-line settings-loading-line-long" />
        </div>
      ))}
    </div>
  );
};
