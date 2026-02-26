import type React from 'react';

interface SettingsAlertProps {
  title: string;
  message: string;
  variant?: 'error' | 'success' | 'warning';
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export const SettingsAlert: React.FC<SettingsAlertProps> = ({
  title,
  message,
  variant = 'error',
  actionLabel,
  onAction,
  className = '',
}) => {
  return (
    <div className={`settings-alert settings-alert-${variant} ${className}`} role="alert">
      <p className="settings-alert-title">{title}</p>
      <p className="settings-alert-msg">{message}</p>
      {actionLabel && onAction ? (
        <button type="button" className="settings-alert-action" onClick={onAction}>
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
};
