/**
 * i18n Navigation utilities for Cirkelline UI
 */

import { locales, defaultLocale, type Locale } from './config';

export function getLocalizedPath(path: string, locale: Locale): string {
  // Remove any existing locale prefix
  const cleanPath = path.replace(new RegExp(`^/(${locales.join('|')})`), '');

  // Don't add locale prefix for default locale
  if (locale === defaultLocale) {
    return cleanPath || '/';
  }

  return `/${locale}${cleanPath || ''}`;
}

export function removeLocaleFromPath(path: string): string {
  return path.replace(new RegExp(`^/(${locales.join('|')})`), '') || '/';
}

export function getAlternateLinks(path: string): Array<{ locale: Locale; href: string }> {
  const cleanPath = removeLocaleFromPath(path);

  return locales.map((locale) => ({
    locale,
    href: getLocalizedPath(cleanPath, locale),
  }));
}
