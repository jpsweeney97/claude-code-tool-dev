import { parse as parseYaml } from 'yaml';

export interface Frontmatter {
  category?: string;
  tags?: string[];
  topic?: string;
  id?: string;
  requires?: string[];
  /**
   * Related document IDs.
   * Note: Uses snake_case to match YAML frontmatter field names.
   */
  related_to?: string[];
}

export interface ParseWarning {
  file: string;
  issue: string;
}

export interface ParseResult {
  frontmatter: Frontmatter;
  body: string;
  warnings: ParseWarning[];
}

// Deprecated global state - kept for backward compatibility
const parseWarnings: ParseWarning[] = [];

/** @deprecated Use warnings returned from parseFrontmatter() */
export function getParseWarnings(): ParseWarning[] {
  return [...parseWarnings];
}

/** @deprecated Use warnings returned from parseFrontmatter() */
export function clearParseWarnings(): void {
  parseWarnings.length = 0;
}

/**
 * Parse a field that can be either a single string or an array of strings.
 * Returns undefined if the field is not present or has invalid type.
 */
function parseStringArrayField(
  value: unknown,
  fieldName: string,
  filePath: string,
  warnings: ParseWarning[],
): string[] | undefined {
  if (value === undefined) {
    return undefined;
  }

  if (typeof value === 'string') {
    return [value];
  }

  if (Array.isArray(value)) {
    const result: string[] = [];
    for (const item of value) {
      if (typeof item === 'string') {
        result.push(item);
      } else {
        warnings.push({
          file: filePath,
          issue: `Invalid ${fieldName} item type: expected string, got ${typeof item}`,
        });
      }
    }
    return result.length > 0 ? result : undefined;
  }

  warnings.push({
    file: filePath,
    issue: `Invalid ${fieldName} type: expected string or array, got ${typeof value}`,
  });
  return undefined;
}

export function parseFrontmatter(
  content: string,
  filePath: string,
): ParseResult {
  // Local warnings array - no global state mutation
  const warnings: ParseWarning[] = [];

  // Normalize line endings to LF for consistent parsing
  const normalized = content.replace(/\r\n/g, '\n');
  const match = normalized.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
  if (!match) return { frontmatter: {}, body: normalized, warnings };

  try {
    const yaml = parseYaml(match[1]);

    // Parse tags with strict type checking
    let tags: string[] = [];
    if (Array.isArray(yaml.tags)) {
      tags = yaml.tags.filter((t: unknown): t is string => {
        if (typeof t === 'string') return true;
        warnings.push({
          file: filePath,
          issue: `Non-string tag value ignored: ${typeof t}`,
        });
        return false;
      });
    } else if (typeof yaml.tags === 'string') {
      tags = [yaml.tags];
    } else if (yaml.tags !== undefined) {
      warnings.push({
        file: filePath,
        issue: `Invalid tags type: expected string or array, got ${typeof yaml.tags}`,
      });
    }

    // Validate category is string
    let category: string | undefined;
    if (typeof yaml.category === 'string') {
      category = yaml.category;
    } else if (yaml.category !== undefined) {
      warnings.push({
        file: filePath,
        issue: `Invalid category type: expected string, got ${typeof yaml.category}`,
      });
    }

    // Validate topic is string
    let topic: string | undefined;
    if (typeof yaml.topic === 'string') {
      topic = yaml.topic;
    } else if (yaml.topic !== undefined) {
      warnings.push({
        file: filePath,
        issue: `Invalid topic type: expected string, got ${typeof yaml.topic}`,
      });
    }

    // Validate id is string
    let id: string | undefined;
    if (typeof yaml.id === 'string') {
      id = yaml.id;
    } else if (yaml.id !== undefined) {
      warnings.push({
        file: filePath,
        issue: `Invalid id type: expected string, got ${typeof yaml.id}`,
      });
    }

    // Parse requires (string or array of strings)
    const requires = parseStringArrayField(yaml.requires, 'requires', filePath, warnings);

    // Parse related_to (string or array of strings)
    const related_to = parseStringArrayField(yaml.related_to, 'related_to', filePath, warnings);

    // Also push to deprecated global for backward compatibility
    parseWarnings.push(...warnings);

    return {
      frontmatter: {
        category,
        tags: tags.length > 0 ? tags : undefined,
        topic,
        id,
        requires,
        related_to,
      },
      body: match[2],
      warnings,
    };
  } catch (err) {
    warnings.push({
      file: filePath,
      issue: `Invalid YAML frontmatter: ${err instanceof Error ? err.message : 'unknown error'}`,
    });
    // Also push to deprecated global for backward compatibility
    parseWarnings.push(...warnings);
    return { frontmatter: {}, body: content, warnings };
  }
}

export function formatMetadataHeader(fm: Frontmatter): string {
  const lines: string[] = [];
  // v2 order: Topic first, then ID, then Category, Tags
  if (fm.topic) lines.push(`Topic: ${fm.topic}`);
  if (fm.id) lines.push(`ID: ${fm.id}`);
  if (fm.category) lines.push(`Category: ${fm.category}`);
  if (fm.tags?.length) lines.push(`Tags: ${fm.tags.join(', ')}`);
  return lines.length ? lines.join('\n') + '\n\n' : '';
}

export function deriveCategory(path: string): string {
  const match = path.match(/^([^/]+)\//);
  return match?.[1] ?? 'general';
}
