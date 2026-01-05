"""ChromaDB semantic search for session summaries."""

import sys
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings


def get_chroma_path() -> Path:
    """Get the path to the ChromaDB storage directory."""
    db_dir = Path.home() / ".claude" / "session-log" / "chroma"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir


def get_collection(db_path: Path | None = None) -> chromadb.Collection:
    """Get or create the sessions collection.

    Args:
        db_path: Optional override for ChromaDB storage path (for testing).

    Returns:
        ChromaDB collection for session embeddings.
    """
    if db_path is None:
        db_path = get_chroma_path()

    settings = Settings(
        persist_directory=str(db_path),
        anonymized_telemetry=False,
    )
    client = chromadb.PersistentClient(path=str(db_path), settings=settings)
    return client.get_or_create_collection(name="sessions")


def embed_session(
    session_id: str,
    content: str,
    metadata: dict | None = None,
    db_path: Path | None = None,
) -> tuple[bool, str | None]:
    """Embed and store a session summary.

    Args:
        session_id: Unique session identifier (used as ChromaDB ID).
        content: Session summary text to embed.
        metadata: Optional metadata dict (project, branch, date, etc.).
        db_path: Optional override for ChromaDB storage path (for testing).

    Returns:
        Tuple of (success, error_message). error_message is None on success.
    """
    try:
        collection = get_collection(db_path)
        collection.upsert(
            ids=[session_id],
            documents=[content],
            metadatas=[metadata] if metadata else None,
        )
        return True, None
    except ValueError as e:
        error_msg = f"Invalid embedding input: {e}"
        print(f"embed_session failed: {error_msg}", file=sys.stderr)
        return False, error_msg
    except RuntimeError as e:
        error_msg = f"ChromaDB runtime error: {e}"
        print(f"embed_session failed: {error_msg}", file=sys.stderr)
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(f"embed_session failed: {error_msg}", file=sys.stderr)
        return False, error_msg


def search_sessions(
    query: str,
    limit: int = 10,
    project: str | None = None,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Search sessions by semantic similarity.

    Args:
        query: Natural language search query.
        limit: Maximum number of results to return.
        project: Optional filter by project name.
        db_path: Optional override for ChromaDB storage path (for testing).

    Returns:
        List of dicts with id, content, metadata, and distance.
        Returns empty list on error.
    """
    try:
        collection = get_collection(db_path)

        if collection.count() == 0:
            return []

        where_filter = {"project": project} if project else None

        results = collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_filter,
        )

        # Flatten results (query returns nested lists)
        output = []
        if results["ids"] and results["ids"][0]:
            for i, session_id in enumerate(results["ids"][0]):
                output.append({
                    "id": session_id,
                    "content": results["documents"][0][i] if results["documents"] else None,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else None,
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })

        return output
    except ValueError as e:
        print(f"search_sessions failed: Invalid query: {e}", file=sys.stderr)
        return []
    except RuntimeError as e:
        print(f"search_sessions failed: ChromaDB error: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"search_sessions failed: {e}", file=sys.stderr)
        return []
