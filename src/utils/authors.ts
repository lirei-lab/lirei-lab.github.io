// Match a publication author string ("F. Last", "F. M. Last-Name") to a team
// member's full name. Accent-insensitive; requires the member's first initial
// to appear among the author's initials and at least one surname token to
// overlap (handles compound Spanish surnames where the paper uses the first).

function normalize(s: string): string {
  return s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
}

function tokens(s: string): string[] {
  return normalize(s)
    .split(/[\s.\-]+/)
    .filter(Boolean);
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
