import React from 'react';
import { useTranslation } from 'react-i18next';

function Dashboard() {
  const { t } = useTranslation();

  return (
    <div className="dashboard">
      <h2>{t('dashboard')}</h2>
      <div className="dashboard-stats">
        <div className="stat-card">
          <h3>{t('totalUsers')}</h3>
          <p>0</p>
        </div>
        <div className="stat-card">
          <h3>{t('totalPayments')}</h3>
          <p>0</p>
        </div>
        <div className="stat-card">
          <h3>{t('activeUsers')}</h3>
          <p>0</p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard; 