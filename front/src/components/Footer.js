import React from 'react';
import { useTranslation } from 'react-i18next';

function Footer() {
  const { t } = useTranslation();

  return (
    <footer className="footer">
      <div className="footer-content">
        <p>&copy; 2025 moonvpn. {t('allRightsReserved')}</p>
      </div>
    </footer>
  );
}

export default Footer; 