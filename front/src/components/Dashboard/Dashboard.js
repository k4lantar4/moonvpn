import React from 'react';
import { useTranslation } from 'react-i18next';
import { FaChartLine, FaUsers, FaShoppingCart, FaCoins } from 'react-icons/fa';
import './Dashboard.css';

const Dashboard = () => {
  const { t } = useTranslation();

  const stats = [
    {
      icon: <FaChartLine />,
      title: t('dashboard.stats.total_sales'),
      value: '0',
      change: '+0%',
      trend: 'up'
    },
    {
      icon: <FaUsers />,
      title: t('dashboard.stats.active_users'),
      value: '0',
      change: '+0%',
      trend: 'up'
    },
    {
      icon: <FaShoppingCart />,
      title: t('dashboard.stats.total_orders'),
      value: '0',
      change: '+0%',
      trend: 'up'
    },
    {
      icon: <FaCoins />,
      title: t('dashboard.stats.total_points'),
      value: '0',
      change: '+0%',
      trend: 'up'
    }
  ];

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1 className="dashboard-title">{t('dashboard.title')}</h1>
        <p className="dashboard-subtitle">{t('dashboard.subtitle')}</p>
      </div>

      <div className="dashboard-stats">
        {stats.map((stat, index) => (
          <div key={index} className="stat-card">
            <div className="stat-icon">{stat.icon}</div>
            <div className="stat-content">
              <h3 className="stat-title">{stat.title}</h3>
              <div className="stat-value">{stat.value}</div>
              <div className={`stat-change ${stat.trend}`}>
                {stat.change}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="dashboard-content">
        <div className="dashboard-section">
          <h2 className="section-title">{t('dashboard.recent_activity')}</h2>
          <div className="empty-state">
            <p>{t('dashboard.no_activity')}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 