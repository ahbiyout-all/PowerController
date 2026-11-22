export type AppLang = 'ko' | 'en';

export const LANG_STORAGE_KEY = 'power_lang';

/**
 * Detects the user's preferred language from browser / OS locale settings.
 * Returns 'ko' when a Korean locale (e.g. 'ko', 'ko-KR') is detected,
 * otherwise defaults to 'en'.
 */
export function detectBrowserLanguage(): { lang: AppLang; detectedLocale: string } {
  const candidates: string[] = [];

  if (typeof navigator !== 'undefined') {
    if (Array.isArray(navigator.languages)) {
      candidates.push(...navigator.languages);
    }
    if (navigator.language) {
      candidates.push(navigator.language);
    }
    const legacyLang = (navigator as unknown as { userLanguage?: string }).userLanguage;
    if (legacyLang) {
      candidates.push(legacyLang);
    }
  }

  try {
    const intlLocale = Intl.DateTimeFormat().resolvedOptions().locale;
    if (intlLocale) {
      candidates.push(intlLocale);
    }
  } catch {
    // Ignore Intl errors in restricted runtimes
  }

  const detectedLocale = candidates.find(Boolean) || 'en-US';

  for (const locale of candidates) {
    const normalized = String(locale).trim().toLowerCase();
    if (normalized === 'ko' || normalized.startsWith('ko-') || normalized.startsWith('ko_')) {
      return { lang: 'ko', detectedLocale };
    }
    if (normalized === 'en' || normalized.startsWith('en-') || normalized.startsWith('en_')) {
      return { lang: 'en', detectedLocale };
    }
  }

  return { lang: 'en', detectedLocale };
}

/**
 * Resolves the initial language: uses persisted manual preference if present,
 * otherwise automatically detects from the browser/OS locale on first visit.
 */
export function getInitialLanguage(): {
  lang: AppLang;
  source: 'manual' | 'auto';
  detectedLocale: string;
} {
  const detected = detectBrowserLanguage();
  try {
    const saved = localStorage.getItem(LANG_STORAGE_KEY);
    if (saved === 'ko' || saved === 'en') {
      return { lang: saved, source: 'manual', detectedLocale: detected.detectedLocale };
    }
  } catch {
    // Ignore storage access errors
  }
  return { lang: detected.lang, source: 'auto', detectedLocale: detected.detectedLocale };
}

export function saveLanguagePreference(lang: AppLang): void {
  try {
    localStorage.setItem(LANG_STORAGE_KEY, lang);
  } catch {
    // Ignore storage access errors
  }
}

export function clearLanguagePreference(): AppLang {
  try {
    localStorage.removeItem(LANG_STORAGE_KEY);
  } catch {
    // Ignore storage access errors
  }
  return detectBrowserLanguage().lang;
}

/**
 * Synchronizes <html lang>, document.title, and description meta tags
 * with the active application language.
 */
export function syncDocumentLanguage(lang: AppLang, appVersion: string): void {
  if (typeof document === 'undefined') return;

  document.documentElement.lang = lang;

  const title =
    lang === 'en'
      ? `PowerController v${appVersion} — Smart Power & Remote Scheduler`
      : `PowerController v${appVersion} — 스마트 전원 제어 및 원격 스케줄러`;
  document.title = title;

  const description =
    lang === 'en'
      ? 'Smart remote power controller, scheduler, and Windows PC management dashboard (Native Desktop & Web UI).'
      : '스마트 원격 전원 제어, 스케줄러 및 시스템 관리 대시보드 (Windows PC Native & Web Dashboard)';

  const metaDesc = document.querySelector('meta[name="description"]');
  if (metaDesc) metaDesc.setAttribute('content', description);

  const ogTitle = document.querySelector('meta[property="og:title"]');
  if (ogTitle) ogTitle.setAttribute('content', `PowerController v${appVersion}`);

  const ogDesc = document.querySelector('meta[property="og:description"]');
  if (ogDesc) ogDesc.setAttribute('content', description);
}
