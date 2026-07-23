import fr from './fr.json';
import en from './en.json';

export const languages = { fr: 'FR', en: 'EN' } as const;
export type Lang = keyof typeof languages;

const dict: Record<Lang, unknown> = { fr, en };

export function useTranslations(lang: Lang) {
  return function t(key: string): string {
    const v = key.split('.').reduce<any>((o, k) => (o ?? {})[k], dict[lang]);
    return typeof v === 'string' ? v : key;
  };
}

export function otherLang(lang: Lang): Lang {
  return lang === 'fr' ? 'en' : 'fr';
}

// Route slugs differ per language; keys are stable identifiers.
export const routes = {
  home: { fr: '', en: '' },
  lab: { fr: 'laboratoire', en: 'laboratory' },
  team: { fr: 'equipe', en: 'team' },
  research: { fr: 'recherche', en: 'research' },
  projects: { fr: 'projets', en: 'projects' },
  publications: { fr: 'publications', en: 'publications' },
  contact: { fr: 'contact', en: 'contact' },
} as const;
export type RouteKey = keyof typeof routes;

export const navOrder: RouteKey[] = [
  'home',
  'lab',
  'team',
  'research',
  'projects',
  'publications',
  'contact',
];

const BASE = import.meta.env.BASE_URL.replace(/\/$/, '');

export function href(lang: Lang, key: RouteKey): string {
  const slug = routes[key][lang];
  const prefix = lang === 'fr' ? '' : '/en';
  return `${BASE}${prefix}/${slug}` || '/';
}
