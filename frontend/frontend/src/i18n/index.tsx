import React, { createContext, useContext, useMemo, useState } from 'react';
import fr from './fr.json';
import en from './en.json';

type Messages = Record<string, string>;

const locales: Record<string, Messages> = {
  fr,
  en,
};

type I18nContextType = {
  t: (key: string, fallback?: string) => string;
  locale: string;
  setLocale: (l: string) => void;
};

const I18nContext = createContext<I18nContextType>({
  t: (k) => k,
  locale: 'fr',
  setLocale: () => {},
});

export function I18nProvider({ children, locale: initialLocale = 'fr' }: { children: React.ReactNode; locale?: string }) {
  const [locale, setLocale] = useState(initialLocale);
  const messages = locales[locale] || {};

  const t = useMemo(() => (key: string, fallback?: string) => {
    return messages[key] ?? fallback ?? key;
  }, [messages]);

  return (
    <I18nContext.Provider value={{ t, locale, setLocale }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useTranslation() {
  return useContext(I18nContext);
}

export default I18nContext;
