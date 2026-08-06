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

/** Does this author string credit this person?
 *
 *  The heuristic below reads names, and names are ambiguous: it cannot tell a
 *  middle name from a first surname, so it accepts any surname token. That is
 *  right for the six people here who sign in more than one form — A. Cárdenas
 *  and A. C. Gonzalez are the same man — but it also handed "C. Henao" to
 *  Carolina Vargas Henao, who signs "C. Vargas". A person carrying
 *  `authorNames` states their signatures instead of being guessed at.
 */
export function authorMatchesPerson(
  person: { name: string; authorNames?: string[] },
  author: string
): boolean {
  if (person.authorNames?.length) {
    const a = tokens(author).join(' ');
    return person.authorNames.some((form) => tokens(form).join(' ') === a);
  }
  return authorMatchesMember(person.name, author);
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

export interface Person {
  slug: string;
  name: string;
  authorNames?: string[];
}

let peopleCache: Promise<Person[]> | null = null;

/** Everyone the catalogue can be filtered by: current members and graduates.
 *
 *  Memoised because every publication asks for it, and the answer is the same
 *  for the whole build.
 */
export function allPeople(): Promise<Person[]> {
  peopleCache ??= (async () => {
    const [team, alumni] = await Promise.all([
      getCollection('team'),
      getCollection('alumni'),
    ]);
    const byslug = new Map<string, Person>();
    for (const entry of [...team, ...alumni]) {
      const slug = personSlug(entry.data.name);
      const known = byslug.get(slug);
      byslug.set(slug, {
        slug,
        name: entry.data.name,
        // A person may hold two entries — a graduate who stayed on as a
        // postdoc. Either may carry the signatures; keep whichever does.
        authorNames: entry.data.authorNames ?? known?.authorNames,
      });
    }
    return [...byslug.values()];
  })();
  return peopleCache;
}

/** The people credited on a publication, as slugs. */
export async function peopleOf(authors: string[]): Promise<string[]> {
  return (await allPeople())
    .filter((p) => authors.some((a) => authorMatchesPerson(p, a)))
    .map((p) => p.slug);
}
