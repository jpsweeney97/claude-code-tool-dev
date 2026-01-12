export interface MarkdownFile {
  path: string; // Relative to docs root: "hooks/input-schema.md"
  content: string;
}

export interface Chunk {
  id: string; // "hooks-input-schema#pretooluse-input"
  content: string; // Includes metadata header + markdown content
  tokens: string[]; // Pre-tokenized content for BM25 scoring
  termFreqs: Map<string, number>; // Precomputed term frequencies for O(1) lookup
  category: string; // From frontmatter or derived from path
  tags: string[]; // From frontmatter (for debugging/filtering)
  source_file: string; // "hooks/input-schema.md"
  heading?: string; // H2 heading if split chunk
  merged_headings?: string[]; // All headings if chunks were merged
}

export interface SearchResult {
  chunk_id: string;
  content: string;
  category: string;
  source_file: string;
}
