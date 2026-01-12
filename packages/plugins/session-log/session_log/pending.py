"""Process pending session files for deferred indexing."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .storage import index_session
from .search import embed_session


def get_pending_dir() -> Path:
    """Get directory for pending session files."""
    pending_dir = Path.home() / ".claude" / "session-log" / "pending"
    pending_dir.mkdir(parents=True, exist_ok=True)
    return pending_dir


def write_pending_metadata(
    filename: str,
    metadata: dict,
    embedding_data: dict,
    pending_dir: Path | None = None,
) -> tuple[bool, str | None]:
    """Write pending metadata for deferred indexing.

    Args:
        filename: The session filename (used as pending file basename).
        metadata: SQLite metadata dict.
        embedding_data: Dict with 'content' and 'metadata' for ChromaDB.
        pending_dir: Optional override for pending directory (for testing).

    Returns:
        Tuple of (success, error_message).
    """
    if pending_dir is None:
        pending_dir = get_pending_dir()

    pending_file = pending_dir / f"{filename}.json"

    pending_data = {
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata,
        "embedding": embedding_data,
    }

    try:
        pending_file.write_text(json.dumps(pending_data, indent=2))
        return True, None
    except OSError as e:
        return False, f"Failed to write pending file: {e}"


def process_pending_sessions(
    pending_dir: Path | None = None,
    db_path: Path | None = None,
    chroma_path: Path | None = None,
) -> dict:
    """Process all pending session files.

    For each pending file:
    1. Index in SQLite
    2. Embed in ChromaDB
    3. Delete pending file if both succeed

    Args:
        pending_dir: Optional override for pending directory (for testing).
        db_path: Optional override for SQLite path (for testing).
        chroma_path: Optional override for ChromaDB path (for testing).

    Returns:
        Dict with counts: processed, indexed, embedded, failed, deleted.
    """
    if pending_dir is None:
        pending_dir = get_pending_dir()

    if not pending_dir.exists():
        return {"processed": 0, "indexed": 0, "embedded": 0, "failed": 0, "deleted": 0}

    stats = {"processed": 0, "indexed": 0, "embedded": 0, "failed": 0, "deleted": 0}

    for pending_file in pending_dir.glob("*.json"):
        stats["processed"] += 1

        try:
            data = json.loads(pending_file.read_text())
        except (json.JSONDecodeError, OSError) as e:
            print(
                f"Warning: Skipping malformed pending file {pending_file.name}: {e}",
                file=sys.stderr,
            )
            pending_file.unlink(missing_ok=True)
            stats["failed"] += 1
            continue

        version = data.get("version", 1)
        if version != 1:
            print(
                f"Warning: Unknown pending file version {version}, skipping",
                file=sys.stderr,
            )
            stats["failed"] += 1
            continue

        metadata = data.get("metadata", {})
        embedding = data.get("embedding", {})

        # Index in SQLite
        indexed, index_error = index_session(metadata, db_path=db_path)
        if indexed:
            stats["indexed"] += 1
        else:
            print(
                f"Warning: Failed to index {pending_file.name}: {index_error}",
                file=sys.stderr,
            )

        # Embed in ChromaDB
        embedded, embed_error = embed_session(
            session_id=metadata.get("filename", pending_file.stem),
            content=embedding.get("content", ""),
            metadata=embedding.get("metadata"),
            db_path=chroma_path,
        )
        if embedded:
            stats["embedded"] += 1
        else:
            print(
                f"Warning: Failed to embed {pending_file.name}: {embed_error}",
                file=sys.stderr,
            )

        # Delete only if both succeeded
        if indexed and embedded:
            pending_file.unlink(missing_ok=True)
            stats["deleted"] += 1

    return stats
