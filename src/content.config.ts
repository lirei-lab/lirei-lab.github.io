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
    axis: z.enum(['smartgrids', 'residential', 'ml', 'hydrogen', 'flexibility', 'ev']),
    status: z.enum(['active', 'completed']),
    partners: z.array(z.string()).default([]),
    team: z.string().optional(),
    image: z.string().optional(),
    imageAlt: bilingual.optional(),
    featured: z.boolean().default(false),
    order: z.number().default(100),
  }),
});

export const collections = { team, publications, projects };
