import { defineCollection, reference, z } from 'astro:content';
import type { Loader } from 'astro/loaders';
import { readFile, readdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import matter from 'gray-matter';
import { site } from './site.config';

// ---------------------------------------------------------------------------
// Hygiene rule: NEVER glob recursively. Real files live at a fixed depth;
// anything deeper is noise (.venv, snapshots, eval outputs). That's why we
// read directories at exact levels with fs, not glob.
//   real skills: <repo>/plugins/<plugin>/skills/<skill>/SKILL.md
//   real docs:   <repo>/plugins/<plugin>/docs/<skill>.md
// ---------------------------------------------------------------------------

function repoRootFrom(configRoot: URL): string {
  // configRoot points at .../catalog/ ; the repo root is its parent.
  return fileURLToPath(new URL('../', configRoot));
}

async function listDirs(dir: string): Promise<string[]> {
  if (!existsSync(dir)) return [];
  const entries = await readdir(dir, { withFileTypes: true });
  return entries.filter((e) => e.isDirectory()).map((e) => e.name);
}

// Extracts a short blurb from the doc: the text between the H1 and the first H2.
// Fallback: first non-empty paragraph that isn't a heading.
function extractBlurb(markdown: string): string {
  const body = matter(markdown).content;
  const lines = body.split(/\r?\n/);
  const collected: string[] = [];
  let seenH1 = false;
  for (const raw of lines) {
    const line = raw.trim();
    if (!seenH1) {
      if (line.startsWith('# ')) seenH1 = true;
      continue;
    }
    if (line.startsWith('## ')) break;
    if (line === '') {
      if (collected.length > 0) break; // end of the first paragraph
      continue;
    }
    if (line.startsWith('#')) continue;
    collected.push(line);
  }
  return collected.join(' ').trim();
}

// --- Loader: plugins (groups) -------------------------------------------------
function pluginsLoader(): Loader {
  return {
    name: 'marketplace-plugins',
    async load({ store, parseData, config }) {
      const repo = repoRootFrom(config.root);
      const marketplacePath = path.join(repo, '.claude-plugin', 'marketplace.json');
      const marketplace = JSON.parse(await readFile(marketplacePath, 'utf8')) as {
        plugins: { name: string; source: string; description: string }[];
      };

      store.clear();
      for (const p of marketplace.plugins) {
        const pluginJsonPath = path.join(repo, 'plugins', p.name, '.claude-plugin', 'plugin.json');
        let version = '';
        if (existsSync(pluginJsonPath)) {
          const pj = JSON.parse(await readFile(pluginJsonPath, 'utf8')) as { version?: string };
          version = pj.version ?? '';
        }
        const data = await parseData({
          id: p.name,
          data: {
            name: p.name,
            description: p.description,
            version,
            installCommand: `npx skills add ${site.repo.slug}/plugins/${p.name}/skills`,
          },
        });
        store.set({ id: p.name, data });
      }
    },
  };
}

// --- Loader: skills (items, the main entity) ----------------------------------
function skillsLoader(): Loader {
  return {
    name: 'marketplace-skills',
    async load({ store, parseData, renderMarkdown, config }) {
      const repo = repoRootFrom(config.root);
      const pluginsDir = path.join(repo, 'plugins');

      store.clear();
      const seen = new Set<string>();

      const pluginNames = await listDirs(pluginsDir);
      for (const plugin of pluginNames) {
        const skillsDir = path.join(pluginsDir, plugin, 'skills');
        const skillDirs = await listDirs(skillsDir);
        for (const skillDir of skillDirs) {
          const skillMd = path.join(skillsDir, skillDir, 'SKILL.md');
          if (!existsSync(skillMd)) continue; // a folder without a direct SKILL.md isn't a skill

          if (seen.has(skillDir)) {
            throw new Error(
              `Duplicate skill name across plugins: "${skillDir}". Ids/URLs must be unique.`,
            );
          }
          seen.add(skillDir);

          const fm = matter(await readFile(skillMd, 'utf8'));
          const name = (fm.data.name as string) ?? skillDir;
          const description = String(fm.data.description ?? '').trim();

          const docPath = path.join(pluginsDir, plugin, 'docs', `${skillDir}.md`);
          const hasDoc = existsSync(docPath);

          let blurb = '';
          let rendered;
          if (hasDoc) {
            const docRaw = await readFile(docPath, 'utf8');
            blurb = extractBlurb(docRaw);
            rendered = await renderMarkdown(docRaw, {
              fileURL: new URL(`plugins/${plugin}/docs/${skillDir}.md`, config.root),
            });
          }

          const data = await parseData({
            id: skillDir,
            data: { name, plugin, description, blurb, hasDoc },
          });
          store.set({ id: skillDir, data, rendered });
        }
      }
    },
  };
}

const plugins = defineCollection({
  loader: pluginsLoader(),
  schema: z.object({
    name: z.string(),
    description: z.string(),
    version: z.string(),
    installCommand: z.string(),
  }),
});

const skills = defineCollection({
  loader: skillsLoader(),
  schema: z.object({
    name: z.string(),
    plugin: reference('plugins'),
    description: z.string(),
    blurb: z.string(),
    hasDoc: z.boolean(),
  }),
});

export const collections = { plugins, skills };
