# Catalog — marketplace showcase

Local (Astro) showcase for the marketplace. It's a **pure projection** of the repo's files:
it reads `../.claude-plugin/marketplace.json`, `../plugins/*/.claude-plugin/plugin.json`,
`../plugins/*/skills/*/SKILL.md`, and `../plugins/*/docs/*.md` at build time. **Nothing is
duplicated here** — adding a plugin/skill/doc to the repo updates the catalog on the next build.

## Run locally

```bash
cd catalog
npm install
npm run dev        # http://localhost:4321
npm run build      # generates dist/ + Pagefind search index
npm run preview    # serves dist/ (with search working)
```

## Reskin (single point of change)

All branding lives in `src/site.config.ts` (name, tagline, description, `repoSlug`, author) and
theme tokens live in `src/styles/theme.css`. Swap the logo at `public/logo.svg`. No other part of
the catalog needs to change to turn it into YOUR marketplace.

## Architecture

- **Skill is the catalog's main entity** (grid on the index page); **plugin** is a filter + its own page.
- **The plugin is the install unit**.
- **Card content** = the first paragraph of `docs/<skill>.md`. **Detail page** = the whole doc rendered.
- **A skill without a doc** shows up flagged as *undocumented* (the catalog also works as a completeness dashboard).
- **Search**: Pagefind (client-side, indexed at build time). In `dev` the search box degrades with a warning.

## Loader hygiene rule (important)

`src/content.config.ts` reads files at a **fixed depth** with `fs`, never with a recursive glob.
Real skills are only `plugins/<plugin>/skills/<skill>/SKILL.md` (a SKILL.md directly inside the
skill's folder); anything deeper — `.venv`, `skill-snapshot/`, eval `outputs/docs/` — is noise and
stays out. Real docs are only `plugins/<plugin>/docs/<skill>.md`.
