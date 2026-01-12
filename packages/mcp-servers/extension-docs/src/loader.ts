// src/loader.ts
import { glob } from 'glob';
import { readFile } from 'fs/promises';
import * as path from 'path';
import type { MarkdownFile } from './types.js';

export async function loadMarkdownFiles(docsPath: string): Promise<MarkdownFile[]> {
  const files: MarkdownFile[] = [];
  const pattern = path.join(docsPath, '**/*.md').replace(/\\/g, '/');

  let filePaths: string[];
  try {
    filePaths = await glob(pattern);
  } catch (err) {
    console.error(
      `WARN: Failed to glob ${pattern}: ${err instanceof Error ? err.message : 'unknown'}`,
    );
    return files;
  }

  for (const filePath of filePaths) {
    try {
      const content = await readFile(filePath, 'utf-8');
      const relativePath = path.relative(docsPath, filePath).replace(/\\/g, '/');
      files.push({ path: relativePath, content });
    } catch (err) {
      if (err instanceof Error) {
        console.error(`WARN: Skipping ${filePath}: ${err.message}`);
      }
    }
  }

  return files;
}
