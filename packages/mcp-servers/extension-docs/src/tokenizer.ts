export function tokenize(text: string): string[] {
  return (
    text
      // Split CamelCase: "PreToolUse" → "Pre Tool Use"
      .replace(/([a-z\d])([A-Z])/g, '$1 $2')
      // Handle consecutive capitals: "MCPServer" → "MCP Server"
      .replace(/([A-Z]+)([A-Z][a-z])/g, '$1 $2')
      // Now lowercase
      .toLowerCase()
      // Split on non-alphanumeric (handles hyphens, underscores, punctuation)
      .split(/[^a-z0-9]+/)
      .filter((term) => term.length > 1)
  );
}
