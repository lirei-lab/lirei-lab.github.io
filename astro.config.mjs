import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://lirei-lab.github.io',
  base: process.env.BASE_PATH ?? '/',
  i18n: {
    defaultLocale: 'fr',
    locales: ['fr', 'en'],
    routing: { prefixDefaultLocale: false },
  },
});
