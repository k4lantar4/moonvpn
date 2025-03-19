import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import Backend from 'i18next-http-backend';
import LanguageDetector from 'i18next-browser-languagedetector';

import pointsEN from './locales/en/points.json';
import pointsFA from './locales/fa/points.json';
import sidebarEN from './locales/en/sidebar.json';
import sidebarFA from './locales/fa/sidebar.json';
import dashboardEN from './locales/en/dashboard.json';
import dashboardFA from './locales/fa/dashboard.json';

i18n
  .use(Backend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: 'en',
    debug: process.env.NODE_ENV === 'development',
    interpolation: {
      escapeValue: false,
    },
    resources: {
      en: {
        points: pointsEN,
        sidebar: sidebarEN,
        dashboard: dashboardEN,
      },
      fa: {
        points: pointsFA,
        sidebar: sidebarFA,
        dashboard: dashboardFA,
      },
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    },
  });

export default i18n; 