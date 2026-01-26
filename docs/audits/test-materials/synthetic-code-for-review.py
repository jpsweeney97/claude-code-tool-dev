#!/usr/bin/env python3
"""
User service for managing user accounts.

TEST MATERIAL: This file has planted issues at 3 difficulty levels for testing
the reviewing-code skill. DO NOT FIX - this is test material.

ANSWER KEY (for test evaluation):
    See: docs/audits/test-materials/synthetic-code-answer-key.md
"""
import json
import os
import hashlib
import sqlite3
from datetime import datetime
from typing import Optional

# OBVIOUS FLAW O1: Hardcoded credentials
DATABASE_PASSWORD = "admin123"
API_SECRET = "sk-prod-1234567890abcdef"

# OBVIOUS FLAW O2: Mutable default argument
def get_users(filter_ids: list = []) -> list:
    """Get users, optionally filtered by ID list."""
    if filter_ids:
        return [u for u in _users if u["id"] in filter_ids]
    return _users

# Global state
_users = []


class UserService:
    """Service for managing users."""

    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self.conn = None
        # MEDIUM FLAW M1: Connection opened in __init__ but no cleanup
        self.conn = sqlite3.connect(db_path)

    # OBVIOUS FLAW O3: SQL injection vulnerability
    def find_user(self, username: str) -> Optional[dict]:
        """Find a user by username."""
        cursor = self.conn.cursor()
        query = f"SELECT * FROM users WHERE username = '{username}'"
        cursor.execute(query)
        row = cursor.fetchone()
        if row:
            return {"id": row[0], "username": row[1], "email": row[2]}
        return None

    # MEDIUM FLAW M2: Password stored as MD5 (weak hash)
    def create_user(self, username: str, password: str, email: str) -> dict:
        """Create a new user."""
        password_hash = hashlib.md5(password.encode()).hexdigest()
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
            (username, password_hash, email)
        )
        self.conn.commit()
        return {"username": username, "email": email, "created": True}

    # OBVIOUS FLAW O4: Catching Exception and silently returning None
    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Get user by ID."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "username": row[1], "email": row[2]}
            return None
        except Exception:
            return None  # Silent failure

    # MEDIUM FLAW M3: Race condition in check-then-act
    def update_email(self, user_id: int, new_email: str) -> bool:
        """Update user's email if they exist."""
        user = self.get_user_by_id(user_id)
        if user is None:
            return False
        # Another thread could delete user between check and update
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE users SET email = ? WHERE id = ?",
            (new_email, user_id)
        )
        self.conn.commit()
        return True

    # SUBTLE FLAW H1: Method does too many things (low cohesion)
    def process_user_action(self, action: str, user_id: int, data: dict) -> dict:
        """Process various user actions."""
        if action == "update_profile":
            # Update profile fields
            cursor = self.conn.cursor()
            if "email" in data:
                cursor.execute("UPDATE users SET email = ? WHERE id = ?",
                             (data["email"], user_id))
            if "username" in data:
                cursor.execute("UPDATE users SET username = ? WHERE id = ?",
                             (data["username"], user_id))
            self.conn.commit()
            return {"success": True, "action": "profile_updated"}
        elif action == "send_notification":
            # This method also handles notifications!?
            print(f"Sending notification to user {user_id}: {data.get('message')}")
            return {"success": True, "action": "notification_sent"}
        elif action == "export_data":
            # And data export too
            user = self.get_user_by_id(user_id)
            return {"success": True, "data": json.dumps(user)}
        else:
            return {"success": False, "error": "Unknown action"}

    # SUBTLE FLAW H2: Magic numbers without explanation
    def check_rate_limit(self, user_id: int) -> bool:
        """Check if user is within rate limits."""
        # What do these numbers mean?
        if self._get_request_count(user_id) > 100:
            if self._get_time_window(user_id) < 3600:
                return False
        return True

    def _get_request_count(self, user_id: int) -> int:
        """Get request count for user."""
        return 50  # Stub

    def _get_time_window(self, user_id: int) -> int:
        """Get time window for user."""
        return 1800  # Stub

    # MEDIUM FLAW M4: No input validation on external data
    def import_users(self, json_data: str) -> int:
        """Import users from JSON string."""
        data = json.loads(json_data)
        count = 0
        for user in data["users"]:
            # Directly using untrusted data
            self.create_user(
                user["username"],
                user["password"],
                user["email"]
            )
            count += 1
        return count

    # SUBTLE FLAW H3: Misleading function name - it also modifies state
    def get_or_create_session(self, user_id: int) -> str:
        """Get existing session or create new one."""
        # Name suggests read-only but actually creates session!
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (user_id, created_at) VALUES (?, ?)",
            (user_id, datetime.now().isoformat())
        )
        self.conn.commit()
        return f"session_{cursor.lastrowid}"

    # SUBTLE FLAW H4: Inconsistent error handling across methods
    def delete_user(self, user_id: int) -> dict:
        """Delete a user."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.conn.commit()
        # Returns dict unlike other methods that return bool
        return {"deleted": True, "id": user_id}

    # MEDIUM FLAW M5: No resource cleanup (connection never closed)
    # Compare to __init__ - opens connection but no close method


# SUBTLE FLAW H5: Dead code - function defined but never used
def _legacy_hash_password(password: str) -> str:
    """Old password hashing function."""
    return hashlib.sha1(password.encode()).hexdigest()


# OBVIOUS FLAW O5: Debug code left in production
if os.environ.get("DEBUG"):
    print("DEBUG MODE ENABLED")
    print(f"Database password: {DATABASE_PASSWORD}")
    print(f"API Secret: {API_SECRET}")
