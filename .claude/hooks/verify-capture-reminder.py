#!/usr/bin/env python3
# /// hook
# event: SessionEnd
# timeout: 5000
# ///
"""
SessionEnd hook: Reminds user to run /verify --capture when Claude Code topics
were discussed during the session.

Scans the conversation transcript for Claude Code keywords and outputs a
reminder if significant discussion occurred (3+ keyword matches).

Exit codes:
  0 - Success (reminder output if topics detected)
  1 - Error (non-blocking, logged)
"""
import json
import re
import sys
from pathlib import Path

# Keywords indicating Claude Code discussion
# Organized by category for maintainability
CLAUDE_CODE_KEYWORDS = {
    # Direct references
    "claude code",
    "claude-code",
    # Components
    "hooks",
    "skills",
    "slash commands",
    "mcp servers",
    "subagents",
    "agents",
    # Files
    "skill.md",
    ".mcp.json",
    "settings.json",
    "claude.md",
    # Events
    "pretooluse",
    "posttooluse",
    "sessionstart",
    "sessionend",
    "userpromptsubmit",
    # Technical terms
    "frontmatter",
    "exit code 2",
    "exit code 0",
    "allowed-tools",
    "tool_input",
    "tool_name",
    # Features
    "claude-code-guide",
    "task tool",
    "/verify",
    "/compact",
}

# Minimum keyword matches to trigger reminder
THRESHOLD = 3


def read_transcript(transcript_path: str) -> str:
    """Read and concatenate all message content from transcript JSONL."""
    try:
        path = Path(transcript_path)
        if not path.exists():
            return ""

        content_parts = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    # Extract content from various message formats
                    if "content" in entry:
                        content = entry["content"]
                        if isinstance(content, str):
                            content_parts.append(content)
                        elif isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict) and "text" in item:
                                    content_parts.append(item["text"])
                                elif isinstance(item, str):
                                    content_parts.append(item)
                    # Also check message field
                    if "message" in entry:
                        msg = entry["message"]
                        if isinstance(msg, str):
                            content_parts.append(msg)
                        elif isinstance(msg, dict) and "content" in msg:
                            content_parts.append(str(msg["content"]))
                except json.JSONDecodeError:
                    continue

        return "\n".join(content_parts)
    except Exception:
        return ""


def count_keyword_matches(text: str) -> tuple[int, set[str]]:
    """Count Claude Code keyword matches in text. Returns (count, matched_keywords)."""
    text_lower = text.lower()
    matched = set()

    for keyword in CLAUDE_CODE_KEYWORDS:
        # Use word boundary matching for short keywords to avoid false positives
        if len(keyword) <= 4:
            pattern = rf"\b{re.escape(keyword)}\b"
            if re.search(pattern, text_lower):
                matched.add(keyword)
        else:
            if keyword in text_lower:
                matched.add(keyword)

    return len(matched), matched


def main():
    try:
        data = json.load(sys.stdin)
        transcript_path = data.get("transcript_path", "")

        if not transcript_path:
            # No transcript available, exit silently
            sys.exit(0)

        # Read and analyze transcript
        transcript_text = read_transcript(transcript_path)
        if not transcript_text:
            sys.exit(0)

        match_count, matched_keywords = count_keyword_matches(transcript_text)

        if match_count >= THRESHOLD:
            # Check if /verify --capture was already run this session
            if "/verify --capture" in transcript_text.lower():
                # Already captured, no reminder needed
                sys.exit(0)

            # Output reminder (will be shown as session ends)
            reminder = (
                "\n"
                "---\n"
                "Tip: This session discussed Claude Code topics. "
                "Consider running `/verify --capture` to queue claims for verification.\n"
                f"(Detected {match_count} Claude Code keywords)\n"
                "---"
            )
            print(reminder)

        sys.exit(0)

    except json.JSONDecodeError as e:
        print(f"Hook error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
