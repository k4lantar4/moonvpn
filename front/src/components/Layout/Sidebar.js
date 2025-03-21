import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FaHome, FaCoins, FaCog } from 'react-icons/fa';
import './Sidebar.css';

const Sidebar = () => {
  const { t } = useTranslation();
  const location = useLocation();

  const menuItems = [
    {
      path: '/',
      icon: <FaHome />,
      label: t('sidebar.dashboard')
    },
    {
      path: '/points',
      icon: <FaCoins />,
      label: t('sidebar.points')
    },
    {
      path: '/settings',
      icon: <FaCog />,
      label: t('sidebar.settings')
    }
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h1 className="sidebar-title">moonvpn Bot</h1>
      </div>
      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`sidebar-link ${location.pathname === item.path ? 'active' : ''}`}
          >
            <span className="sidebar-icon">{item.icon}</span>
            <span className="sidebar-label">{item.label}</span>
          </Link>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar; 