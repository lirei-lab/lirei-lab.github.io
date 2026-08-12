// The laboratory's own accounts, in the order they should be shown.
//
// Personal profiles of members do not belong here. This same list is published
// as schema.org `sameAs`, which asserts to search engines that these profiles
// *are* the organisation — a professor's own account would be a false claim.
//
// Adding a network means adding its entry here and its icon to SocialLinks.astro.
// An empty list renders nothing at all, so the site is never left with a stray
// heading above no icons.

export type SocialId = 'linkedin' | 'youtube' | 'x' | 'facebook';

export interface SocialAccount {
  id: SocialId;
  url: string;
  /** Accessible name. The network's own name, so it needs no translation. */
  name: string;
}

export const social: SocialAccount[] = [
  { id: 'linkedin', url: 'https://www.linkedin.com/company/lirei', name: 'LinkedIn' },
];
