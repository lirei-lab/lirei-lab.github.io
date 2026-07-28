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
  labInfra: { fr: 'laboratoire/infrastructures', en: 'laboratory/infrastructure' },
  labPartners: { fr: 'laboratoire/partenaires', en: 'laboratory/partners' },
  team: { fr: 'equipe', en: 'team' },
  alumni: { fr: 'equipe/diplomes', en: 'team/alumni' },
  research: { fr: 'recherche', en: 'research' },
  publications: { fr: 'publications', en: 'publications' },
  news: { fr: 'actualites', en: 'news' },
  contact: { fr: 'contact', en: 'contact' },
} as const;
export type RouteKey = keyof typeof routes;

// Top-level navigation. A hub with children renders a submenu whose first
// entry is the hub page itself, so the parent is always reachable.
export interface NavItem {
  key: RouteKey;
  children?: RouteKey[];
}

export const navTree: NavItem[] = [
  { key: 'home' },
  { key: 'lab', children: ['lab', 'labInfra', 'labPartners'] },
  { key: 'team', children: ['team', 'alumni'] },
  { key: 'research' },
  { key: 'publications' },
  { key: 'news' },
  { key: 'contact' },
];

// Which top-level entry a route belongs to, for the "current section" state.
export function sectionOf(key: RouteKey): RouteKey {
  const parent = navTree.find((i) => i.children?.includes(key));
  return parent ? parent.key : key;
}

const BASE = import.meta.env.BASE_URL.replace(/\/$/, '');

export function href(lang: Lang, key: RouteKey): string {
  const slug = routes[key][lang];
  const prefix = lang === 'fr' ? '' : '/en';
  return `${BASE}${prefix}/${slug}` || '/';
}

// Prefix a public asset path (e.g. /images/…) with the configured base path.
export function assetPath(path: string): string {
  return `${BASE}${path}`;
}

// Format an ISO date (YYYY-MM-DD) into a long localized date.
export function formatDate(iso: string, lang: Lang): string {
  const locale = lang === 'fr' ? 'fr-CA' : 'en-CA';
  const d = new Date(`${iso}T12:00:00`);
  return d.toLocaleDateString(locale, { year: 'numeric', month: 'long', day: 'numeric' });
}
