export type Partner = string | { name: string; url?: string; logo?: string };

export interface NormalizedPartner {
  name: string;
  url?: string;
  logo?: string;
}

export function normalizePartners(partners: Partner[]): NormalizedPartner[] {
  return partners.map((p) => (typeof p === 'string' ? { name: p } : p));
}
