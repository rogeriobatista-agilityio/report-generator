"""
SQLite database for managing settings, recipients, and configuration.
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from contextlib import contextmanager

# Database file path
DB_PATH = Path(__file__).parent.parent / "data" / "settings.db"


def get_db_path() -> Path:
    """Get the database file path, creating the directory if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DB_PATH


@contextmanager
def get_connection():
    """Get a database connection with context management."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_database():
    """Initialize the database schema."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Settings table for key-value pairs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Recipients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                name TEXT,
                type TEXT CHECK(type IN ('to', 'cc')) DEFAULT 'to',
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Reports history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS report_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                date_range TEXT,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_at TIMESTAMP,
                sent_to TEXT,
                status TEXT DEFAULT 'generated'
            )
        """)
        
        conn.commit()


# Settings Management
class SettingsManager:
    """Manage application settings in the database."""
    
    # Default settings
    DEFAULTS = {
        "sender_name": "Report Generator",
        "sender_email": "",
        "email_provider": "gmail",
        "email_username": "",
        "email_password": "",
        "slack_bot_token": "",
        "slack_channel_id": "",
        "groq_api_key": "",
        "report_output_dir": "reports",
    }
    
    @classmethod
    def key_in_db(cls, key: str) -> bool:
        """Return True if the key exists in the database (even with empty value)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM settings WHERE key = ?", (key,))
            return cursor.fetchone() is not None

    @classmethod
    def get(cls, key: str, default: str = None) -> Optional[str]:
        """Get a setting value. Uses DB first, then default/DEFAULTS."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return row["value"]
            return default or cls.DEFAULTS.get(key)
    
    @classmethod
    def set(cls, key: str, value: str, description: str = None):
        """Set a setting value."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO settings (key, value, description, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET 
                    value = excluded.value,
                    description = COALESCE(excluded.description, settings.description),
                    updated_at = CURRENT_TIMESTAMP
            """, (key, value, description))
    
    @classmethod
    def get_all(cls) -> dict:
        """Get all settings."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value, description FROM settings")
            rows = cursor.fetchall()
            
            # Start with defaults, then override with DB values
            settings = cls.DEFAULTS.copy()
            for row in rows:
                settings[row["key"]] = row["value"]
            
            return settings
    
    @classmethod
    def delete(cls, key: str):
        """Delete a setting."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM settings WHERE key = ?", (key,))
    
    @classmethod
    def initialize_from_env(cls):
        """Initialize settings from environment variables (overwrites existing)."""
        import os
        from dotenv import load_dotenv
        
        # Reload .env to get latest values
        load_dotenv(override=True)
        
        env_mappings = {
            "SENDER_NAME": "sender_name",
            "SENDER_EMAIL": "sender_email",
            "EMAIL_PROVIDER": "email_provider",
            "EMAIL_USERNAME": "email_username",
            "EMAIL_PASSWORD": "email_password",
            "SLACK_BOT_TOKEN": "slack_bot_token",
            "SLACK_CHANNEL_ID": "slack_channel_id",
            "GROQ_API_KEY": "groq_api_key",
            "REPORT_OUTPUT_DIR": "report_output_dir",
        }
        
        for env_key, db_key in env_mappings.items():
            value = os.getenv(env_key)
            if value:
                cls.set(db_key, value, f"Imported from {env_key}")


# Recipients Management
class RecipientsManager:
    """Manage email recipients in the database."""
    
    @classmethod
    def add(cls, email: str, name: str = None, recipient_type: str = "to") -> int:
        """Add a new recipient."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO recipients (email, name, type, active)
                VALUES (?, ?, ?, 1)
            """, (email, name, recipient_type))
            return cursor.lastrowid
    
    @classmethod
    def update(cls, recipient_id: int, email: str = None, name: str = None, 
               recipient_type: str = None, active: bool = None):
        """Update a recipient."""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if email is not None:
                updates.append("email = ?")
                params.append(email)
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if recipient_type is not None:
                updates.append("type = ?")
                params.append(recipient_type)
            if active is not None:
                updates.append("active = ?")
                params.append(1 if active else 0)
            
            if updates:
                params.append(recipient_id)
                cursor.execute(
                    f"UPDATE recipients SET {', '.join(updates)} WHERE id = ?",
                    params
                )
    
    @classmethod
    def delete(cls, recipient_id: int):
        """Delete a recipient."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM recipients WHERE id = ?", (recipient_id,))
    
    @classmethod
    def get_all(cls, active_only: bool = False) -> list[dict]:
        """Get all recipients."""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT id, email, name, type, active, created_at FROM recipients"
            if active_only:
                query += " WHERE active = 1"
            query += " ORDER BY type, name, email"
            
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    @classmethod
    def get_by_type(cls, recipient_type: str, active_only: bool = True) -> list[dict]:
        """Get recipients by type (to or cc)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT id, email, name, type FROM recipients WHERE type = ?"
            params = [recipient_type]
            
            if active_only:
                query += " AND active = 1"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    @classmethod
    def get_email_list(cls, recipient_type: str = None) -> list[str]:
        """Get list of email addresses, optionally filtered by type."""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT email, name FROM recipients WHERE active = 1"
            params = []
            
            if recipient_type:
                query += " AND type = ?"
                params.append(recipient_type)
            
            cursor.execute(query, params)
            
            emails = []
            for row in cursor.fetchall():
                if row["name"]:
                    emails.append(f"{row['name']} <{row['email']}>")
                else:
                    emails.append(row["email"])
            
            return emails
    
    @classmethod
    def clear_all(cls):
        """Delete all recipients from the database."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM recipients")
    
    @classmethod
    def initialize_from_env(cls, force: bool = False):
        """Initialize recipients from environment variables.
        
        Args:
            force: If True, clear existing recipients before importing.
        """
        import os
        import re
        from dotenv import load_dotenv
        
        # Reload .env to get latest values
        load_dotenv(override=True)
        
        # Check if we already have recipients (unless forcing)
        if not force and cls.get_all():
            return 0
        
        # Clear existing if forcing
        if force:
            cls.clear_all()
        
        def parse_recipients(value: str) -> list[tuple[str, str]]:
            """Parse 'Name <email>' or 'email' format."""
            if not value:
                return []
            
            results = []
            for part in value.split(","):
                part = part.strip()
                if not part:
                    continue
                
                # Try to parse "Name <email>" format
                match = re.match(r"([^<]+)\s*<([^>]+)>", part)
                if match:
                    results.append((match.group(2).strip(), match.group(1).strip()))
                else:
                    results.append((part, None))
            
            return results
        
        count = 0
        
        # Import TO recipients
        to_recipients = os.getenv("REPORT_RECIPIENTS_TO", "")
        for email, name in parse_recipients(to_recipients):
            cls.add(email, name, "to")
            count += 1
        
        # Import CC recipients
        cc_recipients = os.getenv("REPORT_RECIPIENTS_CC", "")
        for email, name in parse_recipients(cc_recipients):
            cls.add(email, name, "cc")
            count += 1
        
        return count


# Report History Management
class ReportHistoryManager:
    """Manage report generation history."""
    
    @classmethod
    def add(cls, filename: str, date_range: str = None) -> int:
        """Record a generated report."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO report_history (filename, date_range, status)
                VALUES (?, ?, 'generated')
            """, (filename, date_range))
            return cursor.lastrowid
    
    @classmethod
    def mark_sent(cls, report_id: int, sent_to: list[str]):
        """Mark a report as sent."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE report_history 
                SET sent_at = CURRENT_TIMESTAMP, 
                    sent_to = ?,
                    status = 'sent'
                WHERE id = ?
            """, (json.dumps(sent_to), report_id))
    
    @classmethod
    def get_recent(cls, limit: int = 20) -> list[dict]:
        """Get recent report history."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, filename, date_range, generated_at, sent_at, sent_to, status
                FROM report_history
                ORDER BY generated_at DESC
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                item = dict(row)
                if item["sent_to"]:
                    item["sent_to"] = json.loads(item["sent_to"])
                results.append(item)
            
            return results


# Initialize database on module import
init_database()
