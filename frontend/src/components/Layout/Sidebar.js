import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

function Sidebar() {
  const { t } = useTranslation();

  return (
    <aside className="sidebar">
      <nav>
        <ul>
          <li><Link to="/">{t('dashboard')}</Link></li>
          <li><Link to="/users">{t('users')}</Link></li>
          <li><Link to="/payments">{t('payments')}</Link></li>
          <li><Link to="/settings">{t('settings')}</Link></li>
        </ul>
      </nav>
    </aside>
  );
}

export default Sidebar; 