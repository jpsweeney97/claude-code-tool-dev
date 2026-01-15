"""Transcript parser for extracting session data."""

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TranscriptData:
    """Parsed data from a session transcript."""

    tool_calls: list[dict] = field(default_factory=list)
    files_touched: set[str] = field(default_factory=set)
    user_message_count: int = 0
    assistant_message_count: int = 0
    assistant_text: str = ""
    commands_run: list[str] = field(default_factory=list)


def extract_files_from_tool(name: str, input_data: dict) -> set[str]:
    """Extract file paths from tool input."""
    files = set()

    if name in ("Read", "Write", "Edit"):
        if path := input_data.get("file_path"):
            files.add(path)
    elif name == "Glob":
        # Glob doesn't touch specific files, skip
        pass

    return files


def parse_transcript(path: Path) -> TranscriptData:
    """Parse a transcript JSONL file and extract session data."""
    import sys

    result = TranscriptData()
    text_parts = []

    with open(path) as f:
        for line_num, line in enumerate(f, start=1):
            if not line.strip():
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                print(
                    f"Warning: Skipping malformed JSON at line {line_num}: {e}",
                    file=sys.stderr,
                )
                continue

            msg_type = entry.get("type")
            message = entry.get("message", {})

            if msg_type == "user":
                result.user_message_count += 1

            elif msg_type == "assistant":
                result.assistant_message_count += 1
                content = message.get("content", [])

                if isinstance(content, list):
                    for block in content:
                        block_type = block.get("type")

                        if block_type == "tool_use":
                            tool_name = block.get("name", "")
                            tool_input = block.get("input", {})

                            result.tool_calls.append({
                                "name": tool_name,
                                "input": tool_input,
                            })

                            result.files_touched.update(
                                extract_files_from_tool(tool_name, tool_input)
                            )

                            if tool_name == "Bash":
                                if cmd := tool_input.get("command"):
                                    result.commands_run.append(cmd)

                        elif block_type == "text":
                            if text := block.get("text"):
                                text_parts.append(text)

    result.assistant_text = "\n".join(text_parts)
    return result
