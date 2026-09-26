// Centralized branding + taxonomy. Single reskin point: change the values below
// (and the logo at `public/logo.svg`) to turn this boilerplate into YOUR
// marketplace. Nothing else in the site needs to change.

// Repository slug (owner/repo), used to build the `npx skills add` commands.
const repoSlug = 'vitorsolutions/vitorsolucoes-marketplace';

export const site = {
  name: 'Vitor Soluções',
  tagline: 'Plugin and skill marketplace for Claude Code',
  // Logo served from catalog/public/ (root URL). Swap the file to reskin — no code changes needed.
  logo: '/logo.svg',
  description:
    'Browsable showcase of this marketplace\'s plugins and skills — derived directly from the repository files.',
  repo: {
    slug: repoSlug,
    // Installs every skill in the repo (nested under plugins/*/skills/*) — needs --full-depth.
    installAll: `npx skills add ${repoSlug} --full-depth`,
  },
  author: {
    name: 'Vitor Soluções',
    email: 'contato@vitorsolucoes.com',
  },
} as const;

export type SiteConfig = typeof site;
