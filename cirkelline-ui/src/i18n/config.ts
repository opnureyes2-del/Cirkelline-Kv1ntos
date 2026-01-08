/**
 * i18n Configuration for Cirkelline UI
 *
 * Supported locales: Danish (da), English (en), Swedish (sv), German (de), Arabic (ar)
 */

export const locales = ['da', 'en', 'sv', 'de', 'ar'] as const;
export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = 'da';

export const rtlLocales: Locale[] = ['ar'];

export const localeNames: Record<Locale, string> = {
  da: 'Dansk',
  en: 'English',
  sv: 'Svenska',
  de: 'Deutsch',
  ar: 'العربية',
};

export const localeFlags: Record<Locale, string> = {
  da: '🇩🇰',
  en: '🇬🇧',
  sv: '🇸🇪',
  de: '🇩🇪',
  ar: '🇸🇦',
};

export function isRtl(locale: Locale): boolean {
  return rtlLocales.includes(locale);
}

export function getDirection(locale: Locale): 'ltr' | 'rtl' {
  return isRtl(locale) ? 'rtl' : 'ltr';
}

export function isValidLocale(locale: string): locale is Locale {
  return locales.includes(locale as Locale);
}

export function getLocaleFromPath(pathname: string): Locale | null {
  const segments = pathname.split('/');
  const possibleLocale = segments[1];
  return isValidLocale(possibleLocale) ? possibleLocale : null;
}

export function getLocaleFromAcceptLanguage(acceptLanguage: string): Locale {
  const languages = acceptLanguage.split(',');

  for (const lang of languages) {
    const locale = lang.split(';')[0].trim().substring(0, 2).toLowerCase();
    if (isValidLocale(locale)) {
      return locale;
    }
  }

  return defaultLocale;
}
