"""
Configuration management for the report generator.
Supports loading from SQLite database with fallback to environment variables.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_setting(key: str, default: str = None) -> Optional[str]:
    """Get a setting from database first, then fall back to environment variable."""
    try:
        from src.database import SettingsManager
        if SettingsManager.key_in_db(key):
            return SettingsManager.get(key)
    except Exception:
        pass  # Database not available, use env vars
    
    # Map database keys to environment variable names
    env_mapping = {
        "slack_bot_token": "SLACK_BOT_TOKEN",
        "slack_channel_id": "SLACK_CHANNEL_ID",
        "groq_api_key": "GROQ_API_KEY",
        "sender_name": "SENDER_NAME",
        "sender_email": "SENDER_EMAIL",
        "email_provider": "EMAIL_PROVIDER",
        "email_username": "EMAIL_USERNAME",
        "email_password": "EMAIL_PASSWORD",
        "report_output_dir": "REPORT_OUTPUT_DIR",
    }
    
    env_key = env_mapping.get(key, key.upper())
    return os.getenv(env_key, default)


@dataclass
class SlackConfig:
    """Slack API configuration."""
    bot_token: str
    channel_id: str

    @classmethod
    def from_env(cls) -> "SlackConfig":
        """Create configuration from database/environment variables."""
        bot_token = get_setting("slack_bot_token")
        channel_id = get_setting("slack_channel_id")

        if not bot_token:
            raise ValueError("SLACK_BOT_TOKEN is required (set in database or .env)")
        if not channel_id:
            raise ValueError("SLACK_CHANNEL_ID is required (set in database or .env)")

        return cls(bot_token=bot_token, channel_id=channel_id)


@dataclass
class GroqConfig:
    """Groq AI API configuration (optional)."""
    api_key: Optional[str]
    base_url: str = "https://api.groq.com/openai/v1"

    @classmethod
    def from_env(cls) -> "GroqConfig":
        """Create configuration from database/environment variables."""
        return cls(api_key=get_setting("groq_api_key"))

    @property
    def is_available(self) -> bool:
        """Check if Groq AI is configured."""
        return bool(self.api_key)


@dataclass
class ReportConfig:
    """Report generation configuration."""
    sender_name: str
    sender_email: str
    recipients_to: list[str]
    recipients_cc: list[str]

    @classmethod
    def from_env(cls) -> "ReportConfig":
        """Create configuration from database/environment variables."""
        sender_name = get_setting("sender_name", "Report Generator")
        sender_email = get_setting("sender_email", "")
        
        # Try to get recipients from database first
        recipients_to = []
        recipients_cc = []
        
        try:
            from src.database import RecipientsManager
            recipients_to = RecipientsManager.get_email_list("to")
            recipients_cc = RecipientsManager.get_email_list("cc")
        except Exception:
            pass
        
        # Fall back to environment variables if no database recipients
        if not recipients_to:
            recipients_to_str = os.getenv("REPORT_RECIPIENTS_TO", "")
            recipients_to = [r.strip() for r in recipients_to_str.split(",") if r.strip()]
        
        if not recipients_cc:
            recipients_cc_str = os.getenv("REPORT_RECIPIENTS_CC", "")
            recipients_cc = [r.strip() for r in recipients_cc_str.split(",") if r.strip()]

        return cls(
            sender_name=sender_name,
            sender_email=sender_email,
            recipients_to=recipients_to,
            recipients_cc=recipients_cc,
        )
    
    @property
    def all_recipients(self) -> list[str]:
        """Get all recipients (to + cc) for backward compatibility."""
        return self.recipients_to + self.recipients_cc


@dataclass
class EmailConfig:
    """Email sending configuration (optional)."""
    provider: str
    username: str
    password: Optional[str]

    @classmethod
    def from_env(cls) -> "EmailConfig":
        """Create configuration from database/environment variables."""
        return cls(
            provider=get_setting("email_provider", "gmail"),
            username=get_setting("email_username", ""),
            password=get_setting("email_password"),
        )

    @property
    def is_available(self) -> bool:
        """Check if email is configured."""
        return bool(self.username and self.password)


@dataclass
class AppConfig:
    """Main application configuration."""
    slack: SlackConfig
    groq: GroqConfig
    report: ReportConfig
    email: EmailConfig
    output_dir: Optional[str] = None

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create all configurations from database/environment variables."""
        return cls(
            slack=SlackConfig.from_env(),
            groq=GroqConfig.from_env(),
            report=ReportConfig.from_env(),
            email=EmailConfig.from_env(),
            output_dir=get_setting("report_output_dir", "reports"),
        )
