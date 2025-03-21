import React from 'react';
import { useTranslation } from 'react-i18next';

function Users() {
  const { t } = useTranslation();

  return (
    <div className="users">
      <h2>{t('users')}</h2>
      <div className="users-list">
        <p>{t('noUsers')}</p>
      </div>
    </div>
  );
}

export default Users; 