import React from 'react';
import { useTranslation } from 'react-i18next';

function Payments() {
  const { t } = useTranslation();

  return (
    <div className="payments">
      <h2>{t('payments')}</h2>
      <div className="payments-list">
        <p>{t('noPayments')}</p>
      </div>
    </div>
  );
}

export default Payments; 