// src/schemas.ts
import { z } from 'zod';
import { KNOWN_CATEGORIES, CATEGORY_ALIASES } from './categories.js';
import { SearchMetaSchema } from './status.js';

const CATEGORY_VALUES = [...KNOWN_CATEGORIES] as const;

export const SearchInputSchema = z.object({
  query: z
    .string()
    .max(500, 'Query too long: maximum 500 characters')
    .transform((s) => s.trim())
    .pipe(z.string().min(1, 'Query cannot be empty'))
    .describe(
      'Search query — be specific (e.g., "PreToolUse JSON output", "skill frontmatter properties")',
    ),
  limit: z
    .number()
    .int()
    .min(1)
    .max(20)
    .optional()
    .describe('Maximum results to return (default: 5, max: 20)'),
  category: z
    .enum([...CATEGORY_VALUES, ...Object.keys(CATEGORY_ALIASES)] as [string, ...string[]])
    .transform((val) => CATEGORY_ALIASES[val] ?? val)
    .optional()
    .describe('Filter to a specific category (e.g., "hooks", "plugins", "security")'),
});

export const SearchOutputSchema = z.object({
  results: z.array(
    z.object({
      chunk_id: z.string(),
      content: z.string(),
      snippet: z.string(),
      category: z.string(),
      source_file: z.string(),
    }),
  ),
  error: z.string().optional().describe('Error message if search failed'),
  meta: SearchMetaSchema.optional().describe('Provenance and trust metadata for the search index'),
});
