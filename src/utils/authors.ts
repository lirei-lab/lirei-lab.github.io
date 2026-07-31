// Match a publication author string ("F. Last", "F. M. Last-Name") to a team
// member's full name. Accent-insensitive; requires the member's first initial
// to appear among the author's initials and at least one surname token to
// overlap (handles compound Spanish surnames where the paper uses the first).

import { getCollection } from 'astro:content';

function normalize(s: string): string {
  return s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
}

function tokens(s: string): string[] {
  return normalize(s)
    .split(/[\s.\-]+/)
    .filter(Boolean);
}

/** A stable, URL-safe key for a person, derived from their name.
 *
 *  Keyed on the name rather than on a collection entry so that someone holding
 *  two entries — a master's and a doctorate — resolves to one person, and so a
 *  graduate who later joins the team keeps the same link.
 */
export function personSlug(name: string): string {
  return normalize(name).replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

export function authorMatchesMember(memberName: string, author: string): boolean {
  const m = tokens(memberName);
  const a = tokens(author);
  if (!m.length || !a.length) return false;

  const memberInitial = m[0][0];
  const authorInitials = a.filter((t) => t.length === 1);
  const authorSurnames = a.filter((t) => t.length > 1);
  const memberSurnames = m.slice(1);

  const initialOk = authorInitials.length === 0 || authorInitials.includes(memberInitial);
  const surnameOk = authorSurnames.some((s) => memberSurnames.includes(s));
  return initialOk && surnameOk;
}

let peopleCache: Promise<{ slug: string; name: string }[]> | null = null;

/** Everyone the catalogue can be filtered by: current members and graduates.
 *
 *  Memoised because every publication asks for it, and the answer is the same
 *  for the whole build.
 */
export function allPeople(): Promise<{ slug: string; name: string }[]> {
  peopleCache ??= (async () => {
    const [team, alumni] = await Promise.all([
      getCollection('team'),
      getCollection('alumni'),
    ]);
    const names = new Map<string, string>();
    for (const entry of [...team, ...alumni]) {
      names.set(personSlug(entry.data.name), entry.data.name);
    }
    return [...names].map(([slug, name]) => ({ slug, name }));
  })();
  return peopleCache;
}

/** The people credited on a publication, as slugs. */
export async function peopleOf(authors: string[]): Promise<string[]> {
  return (await allPeople())
    .filter((p) => authors.some((a) => authorMatchesMember(p.name, a)))
    .map((p) => p.slug);
}
