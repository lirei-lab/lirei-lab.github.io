import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const bilingual = z.object({ fr: z.string(), en: z.string() });

const team = defineCollection({
  loader: glob({ pattern: '**/*.json', base: './src/content/team' }),
  schema: z.object({
    name: z.string(),
    category: z.enum(['direction', 'professor', 'staff', 'postdoc', 'student']),
    role: bilingual,
    topic: bilingual.optional(),
    affiliation: z.string().optional(),
    email: z.string().optional(),
    phone: z.string().optional(),
    photo: z.string().optional(),
    bio: bilingual.optional(),
    // How this person signs their papers. Set it only where the initial-and-
    // surname heuristic gets it wrong — a namesake in the catalogue, typically.
    // When present it replaces the heuristic entirely: nothing else matches.
    authorNames: z.array(z.string()).optional(),
    project: z.string().optional(),
    order: z.number().default(100),
  }),
});

const publications = defineCollection({
  loader: glob({ pattern: '**/*.json', base: './src/content/publications' }),
  schema: z.object({
    title: z.string(),
    authors: z.array(z.string()),
    venue: z.string().optional(),
    year: z.number(),
    type: z.enum(['journal', 'conference', 'other']),
    doi: z.string().optional(),
    url: z.string().url().optional(),
  }),
});

const projects = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/projects' }),
  schema: z.object({
    title: bilingual,
    summary: bilingual,
    description: bilingual.optional(),
    objective: bilingual.optional(),
    methodology: bilingual.optional(),
    // Program fiche (flagship programs)
    period: z.string().optional(),
    lead: z.string().optional(),
    funding: bilingual.optional(),
    volets: z.array(z.object({ title: bilingual, desc: bilingual })).optional(),
    // Cross-cutting capability. Orthogonal to `program`: a capability may
    // serve several programs, and a program draws on several capabilities.
    competence: z.enum(['smartgrids', 'residential', 'ml', 'hydrogen', 'flexibility', 'ev']),
    program: z.enum(['flexibilite', 'serres', 'communautes']).optional(),
    status: z.enum(['active', 'completed']),
    // A partner is either a plain name or a name with a link.
    partners: z
      .array(
        z.union([
          z.string(),
          z.object({
            name: z.string(),
            url: z.string().url().optional(),
            logo: z.string().optional(),
          }),
        ])
      )
      .default([]),
    team: z.string().optional(),
    image: z.string().optional(),
    imageAlt: bilingual.optional(),
    featured: z.boolean().default(false),
    order: z.number().default(100),
  }),
});

const news = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/news' }),
  schema: z.object({
    title: bilingual,
    date: z.string(),
    summary: bilingual,
    source: z.string().optional(),
    url: z.string().url().optional(),
    image: z.string().optional(),
  }),
});

const alumni = defineCollection({
  loader: glob({ pattern: '**/*.json', base: './src/content/alumni' }),
  schema: z.object({
    name: z.string(),
    degree: z.enum(['phd', 'msc']),
    year: z.number(),
    thesis: z.string().optional(),
    // The manuscript in UQTR's institutional repository, and the UQTR article
    // or defence announcement covering the work.
    manuscript: z.string().url().optional(),
    blog: z.string().url().optional(),
    // How this person signs their papers. Set it only where the initial-and-
    // surname heuristic gets it wrong — a namesake in the catalogue, typically.
    // When present it replaces the heuristic entirely: nothing else matches.
    authorNames: z.array(z.string()).optional(),
    now: bilingual.optional(),
  }),
});

const partners = defineCollection({
  loader: glob({ pattern: '**/*.json', base: './src/content/partners' }),
  schema: z.object({
    name: z.string(),
    region: z.enum(['canada', 'europe', 'latam', 'afrique']),
    order: z.number().default(50),
    url: z.string().url().optional(),
    people: z.array(z.string()).optional(),
    note: bilingual,
    // Position on the world map. Partners that fall within a marker's width of
    // one another share a `site`, which is what the map plots.
    lat: z.number().optional(),
    lon: z.number().optional(),
    site: z.string().optional(),
    siteKey: z.string().optional(),
    // An academic partner belongs in the academic section and nowhere else,
    // so it is kept off the funders-and-industry wall. Set this where an
    // organisation is genuinely both — a utility's research centre that also
    // funds the work.
    industrial: z.boolean().optional(),
  }),
});

const openings = defineCollection({
  loader: glob({ pattern: '**/*.json', base: './src/content/openings' }),
  schema: z.object({
    title: bilingual,
    // What kind of position, and whether it is a dated vacancy ('open') or a
    // standing invitation to apply ('ongoing').
    type: z.enum(['postdoc', 'phd', 'msc', 'internship', 'engineer']),
    status: z.enum(['open', 'ongoing', 'closed']).default('ongoing'),
    summary: bilingual,
    profile: bilingual.optional(),
    programs: z.array(z.enum(['flexibilite', 'serres', 'communautes'])).optional(),
    // A name needs no translation; an arrangement described in prose does.
    // Same shape as a project's partners: either form is accepted.
    supervisor: z.union([z.string(), bilingual]).optional(),
    funding: bilingual.optional(),
    // ISO date; only meaningful for a dated vacancy.
    deadline: z.string().optional(),
    order: z.number().default(50),
  }),
});

export const collections = { team, publications, projects, news, alumni, partners, openings };
