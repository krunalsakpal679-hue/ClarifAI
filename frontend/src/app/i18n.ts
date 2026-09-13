import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import enTranslation from '../i18n/locales/en.json';
import hiTranslation from '../i18n/locales/hi.json';

const resources = {
  en: {
    translation: enTranslation,
  },
  hi: {
    translation: hiTranslation,
  },
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'en',
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
