"""Tool handler logic for session-log MCP server.

This module contains the core tool logic without MCP dependencies,
making it testable with standard pytest without requiring the MCP package.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from session_log.queries import list_sessions as db_list_sessions
from session_log.queries import get_session as db_get_session
from session_log.search import search_sessions as db_search_sessions
from security import validate_summary_path


@dataclass
class ToolResult:
    """Result from a tool call."""

    type: str
    text: str


def _clamp_limit(limit: int | None, default: int, max_limit: int = 1000) -> int:
    """Clamp limit to valid range [1, max_limit]."""
    if limit is None:
        return default
    return min(max(1, limit), max_limit)


# Tool definitions for list_tools
TOOL_DEFINITIONS = [
    {
        "name": "list_sessions",
        "description": "List session summaries with optional filtering by project and date range",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Filter by project name",
                },
                "after": {
                    "type": "string",
                    "description": "Filter sessions after this date (YYYY-MM-DD)",
                },
                "before": {
                    "type": "string",
                    "description": "Filter sessions before this date (YYYY-MM-DD)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 50)",
                    "default": 50,
                },
            },
        },
    },
    {
        "name": "get_session",
        "description": "Get the full content of a specific session by filename",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The session filename",
                },
            },
            "required": ["filename"],
        },
    },
    {
        "name": "search_sessions",
        "description": "Semantic search across session summaries. Find sessions by meaning, not just keywords.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query (e.g., 'authentication bugs', 'database migrations')",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 10)",
                    "default": 10,
                },
                "project": {
                    "type": "string",
                    "description": "Filter by project name",
                },
            },
            "required": ["query"],
        },
    },
]


def get_tool_definitions() -> list[dict]:
    """Return tool definitions."""
    return TOOL_DEFINITIONS


def handle_list_sessions(arguments: dict) -> list[ToolResult]:
    """Handle list_sessions tool call."""
    results = db_list_sessions(
        project=arguments.get("project"),
        after=arguments.get("after"),
        before=arguments.get("before"),
        limit=_clamp_limit(arguments.get("limit"), default=50),
    )
    return [ToolResult(type="text", text=json.dumps(results, indent=2))]


def handle_get_session(arguments: dict) -> list[ToolResult]:
    """Handle get_session tool call."""
    filename = arguments.get("filename")
    if not filename:
        return [ToolResult(type="text", text="Error: filename required")]

    session = db_get_session(filename)
    if session is None:
        return [ToolResult(type="text", text=f"Session not found: {filename}")]

    # Read the actual markdown content with path validation
    summary_path = session.get("summary_path")
    if not summary_path:
        return [ToolResult(type="text", text=f"Error: Session {filename} has no summary_path")]

    validated_path = validate_summary_path(summary_path)
    if not validated_path:
        return [ToolResult(
            type="text",
            text=f"Error: Summary path validation failed for {filename} (path outside allowed directory or does not exist)",
        )]

    try:
        content = Path(validated_path).read_text()
        return [ToolResult(type="text", text=content)]
    except PermissionError:
        return [ToolResult(type="text", text=f"Error: Permission denied reading {filename}")]
    except UnicodeDecodeError:
        return [ToolResult(type="text", text=f"Error: File encoding issue for {filename}")]
    except OSError as e:
        return [ToolResult(type="text", text=f"Error reading session file: {e}")]


def handle_search_sessions(
    arguments: dict,
    chroma_path: Path | None = None,
) -> list[ToolResult]:
    """Handle search_sessions tool call."""
    query = arguments.get("query")
    if not query:
        return [ToolResult(type="text", text="Error: query required")]

    results = db_search_sessions(
        query=query,
        limit=_clamp_limit(arguments.get("limit"), default=10),
        project=arguments.get("project"),
        db_path=chroma_path,
    )

    return [ToolResult(type="text", text=json.dumps(results, indent=2))]


def handle_tool(name: str, arguments: dict) -> list[ToolResult]:
    """Route tool call to appropriate handler."""
    if name == "list_sessions":
        return handle_list_sessions(arguments)
    elif name == "get_session":
        return handle_get_session(arguments)
    elif name == "search_sessions":
        return handle_search_sessions(arguments)
    return [ToolResult(type="text", text=f"Unknown tool: {name}")]
