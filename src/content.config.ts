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
    axis: z.enum(['smartgrids', 'residential', 'ml', 'hydrogen', 'flexibility', 'ev']),
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
    url: z.string().url().optional(),
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
  }),
});

export const collections = { team, publications, projects, news, alumni, partners };
