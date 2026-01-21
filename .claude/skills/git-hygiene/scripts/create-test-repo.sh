#!/usr/bin/env bash
# create-test-repo.sh — Generate a git repo with intentionally messy state
# for testing the git-hygiene skill
#
# Usage: ./create-test-repo.sh [output-dir]
# Default output: /tmp/git-hygiene-test-XXXXXX

set -euo pipefail

# Output directory
if [[ $# -ge 1 ]]; then
    REPO_DIR="$1"
    mkdir -p "$REPO_DIR"
else
    REPO_DIR=$(mktemp -d /tmp/git-hygiene-test-XXXXXX)
fi

echo "Creating test repo at: $REPO_DIR"
cd "$REPO_DIR"

# =============================================================================
# Phase 1: Initialize repo with realistic structure
# =============================================================================

git init --initial-branch=main
git config user.email "test@example.com"
git config user.name "Test User"

# Create base project structure
mkdir -p src/auth src/api src/utils tests/unit tests/integration config docs

# Initial commit: Project setup
cat > README.md << 'EOF'
# Test Project

A sample project for testing git-hygiene skill.
EOF

cat > .gitignore << 'EOF'
# Minimal initial gitignore
*.log
EOF

cat > src/__init__.py << 'EOF'
"""Test project."""
__version__ = "0.1.0"
EOF

cat > src/auth/__init__.py << 'EOF'
"""Authentication module."""
EOF

cat > src/auth/login.py << 'EOF'
"""Login functionality."""

def authenticate(username: str, password: str) -> bool:
    """Authenticate a user."""
    # TODO(implement): Add real authentication
    if not username or not password:
        raise ValueError("Username and password required")
    return username == "admin" and password == "secret"


def validate_token(token: str) -> bool:
    """Validate a JWT token."""
    if not token:
        return False
    # Placeholder validation
    return token.startswith("valid_")
EOF

cat > src/api/__init__.py << 'EOF'
"""API module."""
EOF

cat > src/api/endpoints.py << 'EOF'
"""API endpoint definitions."""

from typing import Dict, Any


def get_user(user_id: int) -> Dict[str, Any]:
    """Fetch user by ID."""
    return {"id": user_id, "name": "Test User", "email": "test@example.com"}


def list_users(limit: int = 10) -> list:
    """List all users."""
    return [get_user(i) for i in range(limit)]


def create_user(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new user."""
    return {"id": 999, **data}
EOF

cat > src/utils/__init__.py << 'EOF'
"""Utility functions."""
EOF

cat > src/utils/helpers.py << 'EOF'
"""Helper utilities."""

import logging

logger = logging.getLogger(__name__)


def format_name(first: str, last: str) -> str:
    """Format a full name."""
    return f"{first} {last}".strip()


def parse_config(path: str) -> dict:
    """Parse a configuration file."""
    logger.info(f"Loading config from {path}")
    return {}
EOF

cat > tests/__init__.py << 'EOF'
"""Test suite."""
EOF

cat > tests/unit/test_auth.py << 'EOF'
"""Unit tests for auth module."""

import pytest
from src.auth.login import authenticate, validate_token


def test_authenticate_valid():
    assert authenticate("admin", "secret") is True


def test_authenticate_invalid():
    assert authenticate("user", "wrong") is False


def test_authenticate_empty_raises():
    with pytest.raises(ValueError):
        authenticate("", "password")


def test_validate_token_valid():
    assert validate_token("valid_abc123") is True


def test_validate_token_invalid():
    assert validate_token("invalid") is False
EOF

cat > config/settings.yaml << 'EOF'
# Application settings
app:
  name: test-project
  debug: false

database:
  host: localhost
  port: 5432
EOF

git add -A
git commit -m "feat: initial project setup"

# =============================================================================
# Phase 2: Build commit history with multiple features
# =============================================================================

# Feature: Add API rate limiting
cat > src/api/middleware.py << 'EOF'
"""API middleware."""

from functools import wraps
from typing import Callable


def rate_limit(calls_per_minute: int = 60) -> Callable:
    """Rate limiting decorator."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # TODO(implement): Add actual rate limiting
            return func(*args, **kwargs)
        return wrapper
    return decorator
EOF

git add src/api/middleware.py
git commit -m "feat(api): add rate limiting middleware"

# Feature: Add logging configuration
cat > config/logging.yaml << 'EOF'
version: 1
disable_existing_loggers: false
formatters:
  standard:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
handlers:
  console:
    class: logging.StreamHandler
    formatter: standard
root:
  level: INFO
  handlers: [console]
EOF

git add config/logging.yaml
git commit -m "feat(config): add logging configuration"

# Bug fix: Handle edge case in authentication
cat > src/auth/login.py << 'EOF'
"""Login functionality."""

def authenticate(username: str, password: str) -> bool:
    """Authenticate a user."""
    if not username or not password:
        raise ValueError("Username and password required")
    # Normalize username for comparison
    username = username.lower().strip()
    return username == "admin" and password == "secret"


def validate_token(token: str) -> bool:
    """Validate a JWT token."""
    if not token or not isinstance(token, str):
        return False
    return token.startswith("valid_")
EOF

git add src/auth/login.py
git commit -m "fix(auth): normalize username and validate token type"

# Documentation update
cat > docs/API.md << 'EOF'
# API Documentation

## Endpoints

### GET /users
List all users.

### GET /users/:id
Fetch a specific user.

### POST /users
Create a new user.
EOF

git add docs/API.md
git commit -m "docs: add API documentation"

# =============================================================================
# Phase 3: Create branches (some merged, some stale)
# =============================================================================

# Branch that will be merged
git checkout -b feature/user-profiles
cat > src/api/profiles.py << 'EOF'
"""User profile endpoints."""

def get_profile(user_id: int) -> dict:
    """Get user profile."""
    return {"user_id": user_id, "bio": "", "avatar": None}
EOF
git add src/api/profiles.py
git commit -m "feat(api): add user profile endpoint"
git checkout main
git merge --no-ff feature/user-profiles -m "Merge branch 'feature/user-profiles'"

# Another merged branch
git checkout -b fix/login-redirect
cat >> src/auth/login.py << 'EOF'


def get_redirect_url(user_id: int) -> str:
    """Get post-login redirect URL."""
    return f"/dashboard/{user_id}"
EOF
git add src/auth/login.py
git commit -m "fix(auth): add post-login redirect"
git checkout main
git merge --no-ff fix/login-redirect -m "Merge branch 'fix/login-redirect'"

# Stale branch (not merged, abandoned)
git checkout -b experiment/caching
cat > src/utils/cache.py << 'EOF'
"""Caching utilities - EXPERIMENTAL."""

class SimpleCache:
    def __init__(self):
        self._store = {}

    def get(self, key):
        return self._store.get(key)

    def set(self, key, value):
        self._store[key] = value
EOF
git add src/utils/cache.py
git commit -m "wip: experimental caching"
git checkout main

# Another stale branch
git checkout -b spike/graphql
cat > docs/graphql-notes.md << 'EOF'
# GraphQL Investigation

## Pros
- Flexible queries
- Single endpoint

## Cons
- Complexity
- Caching harder

## Decision: Not now
EOF
git add docs/graphql-notes.md
git commit -m "spike: graphql investigation notes"
git checkout main

# =============================================================================
# Phase 4: Create untracked mess
# =============================================================================

# Build artifacts
mkdir -p __pycache__ src/__pycache__ src/auth/__pycache__
echo "compiled" > __pycache__/module.cpython-311.pyc
echo "compiled" > src/__pycache__/__init__.cpython-311.pyc
echo "compiled" > src/auth/__pycache__/login.cpython-311.pyc

# Node artifacts (simulated)
mkdir -p node_modules/.cache
echo '{"name": "fake-package"}' > node_modules/package.json
echo "cache data" > node_modules/.cache/data

# Editor/IDE files
mkdir -p .vscode .idea
cat > .vscode/settings.json << 'EOF'
{
    "python.defaultInterpreterPath": "/usr/bin/python3",
    "editor.formatOnSave": true
}
EOF
echo "workspace.xml content" > .idea/workspace.xml
echo "swap file" > src/auth/.login.py.swp

# OS files
echo "" > .DS_Store
echo "" > src/.DS_Store

# Unknown files (need user decision)
cat > notes.md << 'EOF'
# Developer Notes

Remember to:
- Update the API docs
- Add integration tests
- Review the caching approach
EOF

cat > scratch.py << 'EOF'
# Quick test script
from src.auth.login import authenticate

result = authenticate("admin", "secret")
print(f"Auth result: {result}")
EOF

cat > TODO.txt << 'EOF'
- Finish rate limiting implementation
- Add database migrations
- Set up CI/CD
EOF

# PROTECTED FILES - these should trigger warnings
cat > .env.local << 'EOF'
DATABASE_URL=postgres://user:password@localhost:5432/mydb
SECRET_KEY=super-secret-key-12345
API_KEY=sk-1234567890abcdef
EOF

cat > credentials.json << 'EOF'
{
    "aws_access_key": "AKIAIOSFODNN7EXAMPLE",
    "aws_secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}
EOF

mkdir -p secrets
cat > secrets/api.key << 'EOF'
-----BEGIN API KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0Z3VS
-----END API KEY-----
EOF

# =============================================================================
# Phase 5: Create mixed staged/unstaged changes spanning multiple concerns
# =============================================================================

# Concern 1: Auth-related fix (will be staged)
cat > src/auth/login.py << 'EOF'
"""Login functionality."""

import hashlib
import secrets


def authenticate(username: str, password: str) -> bool:
    """Authenticate a user with timing-safe comparison."""
    if not username or not password:
        raise ValueError("Username and password required")
    username = username.lower().strip()
    # Use timing-safe comparison to prevent timing attacks
    expected = hashlib.sha256(b"admin:secret").hexdigest()
    actual = hashlib.sha256(f"{username}:{password}".encode()).hexdigest()
    return secrets.compare_digest(expected, actual)


def validate_token(token: str) -> bool:
    """Validate a JWT token."""
    if not token or not isinstance(token, str):
        return False
    return token.startswith("valid_")


def get_redirect_url(user_id: int) -> str:
    """Get post-login redirect URL."""
    return f"/dashboard/{user_id}"


def refresh_token(old_token: str) -> str:
    """Refresh an expiring token."""
    if not validate_token(old_token):
        raise ValueError("Invalid token cannot be refreshed")
    return f"valid_refreshed_{secrets.token_hex(8)}"
EOF

# Concern 2: Formatting cleanup (will be staged)
cat > src/api/endpoints.py << 'EOF'
"""API endpoint definitions."""

from typing import Any


def get_user(user_id: int) -> dict[str, Any]:
    """Fetch user by ID."""
    return {
        "id": user_id,
        "name": "Test User",
        "email": "test@example.com",
    }


def list_users(limit: int = 10) -> list[dict[str, Any]]:
    """List all users."""
    return [get_user(i) for i in range(limit)]


def create_user(data: dict[str, Any]) -> dict[str, Any]:
    """Create a new user."""
    return {"id": 999, **data}
EOF

# Concern 3: Unrelated refactor (will be staged)
cat > src/utils/helpers.py << 'EOF'
"""Helper utilities."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def format_name(first: str, last: str) -> str:
    """Format a full name, handling edge cases."""
    parts = [p.strip() for p in (first, last) if p and p.strip()]
    return " ".join(parts)


def parse_config(path: str | Path) -> dict:
    """Parse a configuration file.

    Args:
        path: Path to the config file (str or Path object)

    Returns:
        Parsed configuration dictionary
    """
    path = Path(path)
    logger.info(f"Loading config from {path}")
    if not path.exists():
        logger.warning(f"Config file not found: {path}")
        return {}
    return {}


def ensure_directory(path: str | Path) -> Path:
    """Ensure a directory exists, creating if needed."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path
EOF

# Stage all the mixed changes
git add src/auth/login.py src/api/endpoints.py src/utils/helpers.py

# Now add unstaged changes on top (Concern 4: test updates - NOT staged)
cat >> tests/unit/test_auth.py << 'EOF'


def test_refresh_token_valid():
    """Test token refresh with valid token."""
    from src.auth.login import refresh_token
    new_token = refresh_token("valid_old_token")
    assert new_token.startswith("valid_refreshed_")


def test_refresh_token_invalid_raises():
    """Test token refresh with invalid token raises."""
    from src.auth.login import refresh_token
    with pytest.raises(ValueError):
        refresh_token("invalid_token")
EOF

# Concern 5: Config update (NOT staged)
cat >> config/settings.yaml << 'EOF'

security:
  token_expiry_minutes: 60
  max_login_attempts: 5
EOF

# =============================================================================
# Summary
# =============================================================================

echo ""
echo "=============================================="
echo "Test repo created at: $REPO_DIR"
echo "=============================================="
echo ""
echo "UNTRACKED FILES:"
echo "  Build artifacts: __pycache__/, node_modules/, *.pyc"
echo "  Editor files:    .vscode/, .idea/, *.swp"
echo "  OS files:        .DS_Store"
echo "  Unknown:         notes.md, scratch.py, TODO.txt"
echo "  PROTECTED:       .env.local, credentials.json, secrets/"
echo ""
echo "STAGED CHANGES (mixed concerns):"
echo "  - src/auth/login.py      (auth: timing-safe comparison + refresh)"
echo "  - src/api/endpoints.py   (style: type hints formatting)"
echo "  - src/utils/helpers.py   (refactor: Path support + new helper)"
echo ""
echo "UNSTAGED CHANGES:"
echo "  - tests/unit/test_auth.py  (test: new refresh token tests)"
echo "  - config/settings.yaml     (config: security settings)"
echo ""
echo "BRANCHES:"
echo "  main                    - current branch"
echo "  feature/user-profiles   - MERGED"
echo "  fix/login-redirect      - MERGED"
echo "  experiment/caching      - STALE (not merged)"
echo "  spike/graphql           - STALE (not merged)"
echo ""
echo "To test git-hygiene skill:"
echo "  cd $REPO_DIR"
echo "  claude"
echo "  /git-hygiene"
echo ""
