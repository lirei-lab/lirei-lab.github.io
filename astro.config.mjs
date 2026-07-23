import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://www.uqtr.ca',
  base: process.env.BASE_PATH ?? '/',
  i18n: {
    defaultLocale: 'fr',
    locales: ['fr', 'en'],
    routing: { prefixDefaultLocale: false },
  },
});
