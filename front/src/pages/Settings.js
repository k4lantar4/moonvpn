import React from 'react';
import { useTranslation } from 'react-i18next';

function Settings() {
  const { t } = useTranslation();

  return (
    <div className="settings">
      <h2>{t('settings')}</h2>
      <div className="settings-form">
        <div className="form-group">
          <label>{t('botToken')}</label>
          <input type="password" placeholder={t('enterBotToken')} />
        </div>
        <div className="form-group">
          <label>{t('adminId')}</label>
          <input type="text" placeholder={t('enterAdminId')} />
        </div>
        <button type="submit">{t('save')}</button>
      </div>
    </div>
  );
}

export default Settings; 