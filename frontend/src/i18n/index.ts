import i18n from '../app/i18n';

export type SupportedLanguage = 'en' | 'hi';

export const changeLanguage = (lng: SupportedLanguage): Promise<unknown> => {
  return i18n.changeLanguage(lng);
};

export default i18n;
