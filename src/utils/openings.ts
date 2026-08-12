/** The URL slug for an opening.
 *
 *  File names carry a numeric prefix so the collection sorts without a field
 *  for it — `05-phd-acet-hydrogene`. That prefix orders the list; it has no
 *  business in a link someone is meant to share, and it would change the
 *  address if an opening were ever reordered.
 */
export function openingSlug(id: string): string {
  return id.replace(/^\d+-/, '');
}
