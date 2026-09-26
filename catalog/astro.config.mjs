// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

// Marketplace catalog site. Reads the parent repo's plugins/skills (../) at build time.
export default defineConfig({
  site: 'http://localhost:4321',
  vite: {
    plugins: [tailwindcss()],
  },
});
