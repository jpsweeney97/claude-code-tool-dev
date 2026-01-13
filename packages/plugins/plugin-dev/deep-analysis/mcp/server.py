"""
Deep Analysis MCP Server

Provides semantic search and indexing for analysis documents.
Uses txtai for embeddings and SQLite storage.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("deep-analysis-mcp")

# Index location
INDEX_DIR = Path.home() / ".claude" / "deep-analysis" / "index"
GLOBAL_ANALYSES_DIR = Path.home() / ".claude" / "analyses"

# Lazy-loaded txtai embeddings
_embeddings = None


def get_embeddings():
    """Lazy-load txtai embeddings."""
    global _embeddings
    if _embeddings is None:
        try:
            from txtai import Embeddings

            INDEX_DIR.mkdir(parents=True, exist_ok=True)
            index_path = INDEX_DIR / "embeddings"

            _embeddings = Embeddings(
                path="sentence-transformers/all-MiniLM-L6-v2",
                content=True,  # Store content for retrieval
            )

            # Load existing index if it exists
            if index_path.exists():
                _embeddings.load(str(index_path))
                logger.info(f"Loaded existing index from {index_path}")
            else:
                logger.info("No existing index found, starting fresh")

        except ImportError as e:
            logger.error(f"Failed to import txtai: {e}")
            raise RuntimeError(
                "txtai is required but not installed. Run: uv add txtai"
            ) from e

    return _embeddings


def save_index():
    """Save the index to disk."""
    if _embeddings is not None:
        index_path = INDEX_DIR / "embeddings"
        _embeddings.save(str(index_path))
        logger.info(f"Saved index to {index_path}")


def compute_file_hash(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """
    Parse YAML frontmatter from markdown content.

    Returns (frontmatter_dict, body_text).
    Permissive: returns empty dict if no frontmatter or invalid YAML.
    """
    frontmatter: dict[str, Any] = {}
    body = content

    # Check for frontmatter delimiters
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                import yaml

                frontmatter = yaml.safe_load(parts[1]) or {}
            except Exception as e:
                logger.warning(f"Failed to parse YAML frontmatter: {e}")
                frontmatter = {}
            body = parts[2].strip()

    return frontmatter, body


def validate_path(path: str, project_path: str | None = None) -> Path:
    """
    Validate that path is within allowed directories.

    Raises ValueError if path is outside allowed directories.
    """
    resolved = Path(path).resolve()

    # Always allow global analyses directory
    if resolved.is_relative_to(GLOBAL_ANALYSES_DIR):
        return resolved

    # Allow project-specific path if project_path provided
    if project_path:
        project_analysis_dir = Path(project_path).resolve() / "docs" / "analysis"
        if resolved.is_relative_to(project_analysis_dir):
            return resolved

    raise ValueError(
        f"Path must be within allowed directories "
        f"(~/.claude/analyses/ or <project>/docs/analysis/): {path}"
    )


def get_analysis_dirs(project_path: str | None = None) -> list[Path]:
    """Get all directories to scan for analyses."""
    dirs = [GLOBAL_ANALYSES_DIR]

    if project_path:
        project_dir = Path(project_path).resolve() / "docs" / "analysis"
        if project_dir.exists():
            dirs.append(project_dir)

    return dirs


def index_single_file(path: Path) -> dict[str, Any] | None:
    """
    Index a single analysis file.

    Returns the document dict if successful, None if skipped.
    """
    if not path.suffix == ".md":
        return None

    if not path.exists():
        logger.warning(f"File not found: {path}")
        return None

    try:
        content = path.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(content)

        # Extract key fields
        file_hash = compute_file_hash(path)
        problem = frontmatter.get("problem", path.stem)
        date = frontmatter.get("date", "")
        if isinstance(date, datetime):
            date = date.strftime("%Y-%m-%d")
        decision = frontmatter.get("decision", "")
        status = frontmatter.get("status", "unknown")
        domain = frontmatter.get("domain", [])
        keywords = frontmatter.get("keywords", [])

        # Create searchable text
        searchable_text = f"{problem} {body}"
        if keywords:
            searchable_text += " " + " ".join(keywords)

        doc = {
            "id": str(path),
            "path": str(path),
            "text": searchable_text,
            "problem": problem,
            "date": str(date),
            "decision": decision,
            "status": status,
            "domain": domain if isinstance(domain, list) else [domain],
            "hash": file_hash,
        }

        return doc

    except Exception as e:
        logger.error(f"Failed to index {path}: {e}")
        return None


# Create MCP server
server = Server("deep-analysis")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="search_analyses",
            description="Semantic search over indexed analysis documents",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query",
                    },
                    "project_path": {
                        "type": "string",
                        "description": "Optional absolute path to project root. "
                        "If provided, also searches project's docs/analysis/",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return (default 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="index_analysis",
            description="Add or update an analysis document in the index",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the analysis markdown file",
                    },
                    "project_path": {
                        "type": "string",
                        "description": "Optional project path for validation",
                    },
                },
                "required": ["path"],
            },
        ),
        types.Tool(
            name="remove_analysis",
            description="Remove an analysis document from the index",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the analysis to remove",
                    },
                },
                "required": ["path"],
            },
        ),
        types.Tool(
            name="rebuild_index",
            description="Rebuild the entire index by scanning all analysis directories",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Optional project path to include in rebuild",
                    },
                },
            },
        ),
        types.Tool(
            name="list_analyses",
            description="List indexed analyses with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Filter by domain tag (exact match)",
                    },
                    "since": {
                        "type": "string",
                        "description": "Filter by date (YYYY-MM-DD), returns analyses on or after this date",
                    },
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls."""

    if name == "search_analyses":
        return await handle_search_analyses(
            query=arguments["query"],
            project_path=arguments.get("project_path"),
            limit=arguments.get("limit", 5),
        )

    elif name == "index_analysis":
        return await handle_index_analysis(
            path=arguments["path"],
            project_path=arguments.get("project_path"),
        )

    elif name == "remove_analysis":
        return await handle_remove_analysis(path=arguments["path"])

    elif name == "rebuild_index":
        return await handle_rebuild_index(
            project_path=arguments.get("project_path"),
        )

    elif name == "list_analyses":
        return await handle_list_analyses(
            domain=arguments.get("domain"),
            since=arguments.get("since"),
        )

    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


async def handle_search_analyses(
    query: str,
    project_path: str | None = None,
    limit: int = 5,
) -> list[types.TextContent]:
    """Semantic search over indexed analyses."""
    try:
        embeddings = get_embeddings()

        # Check if index has any documents
        if embeddings.count() == 0:
            return [
                types.TextContent(
                    type="text",
                    text="No analyses indexed yet. Use rebuild_index to scan for analyses.",
                )
            ]

        # Perform search
        results = embeddings.search(query, limit=limit)

        if not results:
            return [
                types.TextContent(
                    type="text",
                    text=f"No analyses found matching: {query}",
                )
            ]

        # Format results
        output_lines = [f"Found {len(results)} matching analyses:\n"]

        for i, result in enumerate(results, 1):
            # txtai returns (id, score) or dict depending on content setting
            if isinstance(result, dict):
                doc_id = result.get("id", "unknown")
                score = result.get("score", 0)
                problem = result.get("problem", "unknown")
                date = result.get("date", "unknown")
                decision = result.get("decision", "")
                status = result.get("status", "unknown")
            else:
                doc_id, score = result[0], result[1]
                problem = Path(doc_id).stem if doc_id else "unknown"
                date = ""
                decision = ""
                status = ""

            output_lines.append(f"{i}. **{problem}** (score: {score:.3f})")
            output_lines.append(f"   Path: {doc_id}")
            if date:
                output_lines.append(f"   Date: {date}")
            if decision:
                output_lines.append(f"   Decision: {decision}")
            if status:
                output_lines.append(f"   Status: {status}")
            output_lines.append("")

        return [types.TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"Search failed: {e}")
        return [types.TextContent(type="text", text=f"Search failed: {e}")]


async def handle_index_analysis(
    path: str,
    project_path: str | None = None,
) -> list[types.TextContent]:
    """Index a single analysis file."""
    try:
        validated_path = validate_path(path, project_path)
        embeddings = get_embeddings()

        doc = index_single_file(validated_path)
        if doc is None:
            return [
                types.TextContent(
                    type="text",
                    text=f"Failed to index {path}: file not found or not a markdown file",
                )
            ]

        # Upsert the document
        embeddings.upsert([(doc["id"], doc["text"], None)])
        save_index()

        return [
            types.TextContent(
                type="text",
                text=f"Indexed: {doc['problem']} ({validated_path})",
            )
        ]

    except ValueError as e:
        return [types.TextContent(type="text", text=str(e))]
    except Exception as e:
        logger.error(f"Index failed: {e}")
        return [types.TextContent(type="text", text=f"Index failed: {e}")]


async def handle_remove_analysis(path: str) -> list[types.TextContent]:
    """Remove an analysis from the index."""
    try:
        embeddings = get_embeddings()
        resolved = Path(path).resolve()

        # Delete from index
        embeddings.delete([str(resolved)])
        save_index()

        return [
            types.TextContent(
                type="text",
                text=f"Removed from index: {resolved}",
            )
        ]

    except Exception as e:
        logger.error(f"Remove failed: {e}")
        return [types.TextContent(type="text", text=f"Remove failed: {e}")]


async def handle_rebuild_index(
    project_path: str | None = None,
) -> list[types.TextContent]:
    """Rebuild the entire index."""
    try:
        from txtai import Embeddings

        global _embeddings

        # Create fresh embeddings
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        _embeddings = Embeddings(
            path="sentence-transformers/all-MiniLM-L6-v2",
            content=True,
        )

        # Scan all directories
        dirs = get_analysis_dirs(project_path)
        documents = []
        scanned = 0
        indexed = 0

        for dir_path in dirs:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                continue

            for md_file in dir_path.glob("**/*.md"):
                scanned += 1
                doc = index_single_file(md_file)
                if doc:
                    documents.append((doc["id"], doc["text"], None))
                    indexed += 1

        # Index all documents
        if documents:
            _embeddings.index(documents)

        save_index()

        return [
            types.TextContent(
                type="text",
                text=f"Rebuilt index: scanned {scanned} files, indexed {indexed} analyses",
            )
        ]

    except Exception as e:
        logger.error(f"Rebuild failed: {e}")
        return [types.TextContent(type="text", text=f"Rebuild failed: {e}")]


async def handle_list_analyses(
    domain: str | None = None,
    since: str | None = None,
) -> list[types.TextContent]:
    """List indexed analyses with optional filtering."""
    try:
        # Since txtai doesn't support listing all documents easily,
        # we'll scan the directories directly
        dirs = get_analysis_dirs()
        analyses = []

        for dir_path in dirs:
            if not dir_path.exists():
                continue

            for md_file in dir_path.glob("**/*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    frontmatter, _ = parse_frontmatter(content)

                    doc_date = frontmatter.get("date", "")
                    if isinstance(doc_date, datetime):
                        doc_date = doc_date.strftime("%Y-%m-%d")
                    doc_date = str(doc_date)

                    doc_domain = frontmatter.get("domain", [])
                    if isinstance(doc_domain, str):
                        doc_domain = [doc_domain]

                    # Apply filters
                    if since and doc_date < since:
                        continue

                    if domain and domain not in doc_domain:
                        continue

                    analyses.append(
                        {
                            "path": str(md_file),
                            "problem": frontmatter.get("problem", md_file.stem),
                            "date": doc_date,
                            "status": frontmatter.get("status", "unknown"),
                            "decision": frontmatter.get("decision", ""),
                            "domain": doc_domain,
                        }
                    )

                except Exception as e:
                    logger.warning(f"Failed to read {md_file}: {e}")

        # Sort by date descending
        analyses.sort(key=lambda x: x["date"], reverse=True)

        if not analyses:
            filters = []
            if domain:
                filters.append(f"domain={domain}")
            if since:
                filters.append(f"since={since}")
            filter_str = f" with filters: {', '.join(filters)}" if filters else ""
            return [
                types.TextContent(
                    type="text",
                    text=f"No analyses found{filter_str}",
                )
            ]

        # Format output
        output_lines = [f"Found {len(analyses)} analyses:\n"]

        for analysis in analyses:
            output_lines.append(f"- **{analysis['problem']}** ({analysis['date']})")
            output_lines.append(f"  Status: {analysis['status']}")
            if analysis["decision"]:
                output_lines.append(f"  Decision: {analysis['decision']}")
            output_lines.append(f"  Path: {analysis['path']}")
            output_lines.append("")

        return [types.TextContent(type="text", text="\n".join(output_lines))]

    except Exception as e:
        logger.error(f"List failed: {e}")
        return [types.TextContent(type="text", text=f"List failed: {e}")]


async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
