import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://lirei.ca',
  base: process.env.BASE_PATH ?? '/',
  // Alumni moved under the team section; keep the original URLs working.
  redirects: {
    '/diplomes': '/equipe/diplomes',
    '/en/alumni': '/en/team/alumni',
    // Openings grew into a section of its own and moved out of the team pages.
    '/equipe/offres': '/opportunites',
    '/en/team/openings': '/en/opportunities',
  },
  i18n: {
    defaultLocale: 'fr',
    locales: ['fr', 'en'],
    routing: { prefixDefaultLocale: false },
  },
});
