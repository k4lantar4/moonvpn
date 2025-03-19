import React from 'react';
import { useTranslation } from 'react-i18next';

function Header() {
  const { t } = useTranslation();

  return (
    <header className="header">
      <div className="header-content">
        <h1>moonvpn</h1>
        <nav>
          <ul>
            <li><a href="/">{t('home')}</a></li>
            <li><a href="/users">{t('users')}</a></li>
            <li><a href="/payments">{t('payments')}</a></li>
            <li><a href="/settings">{t('settings')}</a></li>
          </ul>
        </nav>
      </div>
    </header>
  );
}

export default Header; 