import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://lirei-lab.github.io',
  base: process.env.BASE_PATH ?? '/',
  // Alumni moved under the team section; keep the original URLs working.
  redirects: {
    '/diplomes': '/equipe/diplomes',
    '/en/alumni': '/en/team/alumni',
  },
  i18n: {
    defaultLocale: 'fr',
    locales: ['fr', 'en'],
    routing: { prefixDefaultLocale: false },
  },
});
