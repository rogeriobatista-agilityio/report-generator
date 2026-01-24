"""
Configuration management for the report generator.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class SlackConfig:
    """Slack API configuration."""
    bot_token: str
    channel_id: str

    @classmethod
    def from_env(cls) -> "SlackConfig":
        """Create configuration from environment variables."""
        bot_token = os.getenv("SLACK_BOT_TOKEN")
        channel_id = os.getenv("SLACK_CHANNEL_ID")

        if not bot_token:
            raise ValueError("SLACK_BOT_TOKEN environment variable is required")
        if not channel_id:
            raise ValueError("SLACK_CHANNEL_ID environment variable is required")

        return cls(bot_token=bot_token, channel_id=channel_id)


@dataclass
class GroqConfig:
    """Groq AI API configuration (optional)."""
    api_key: Optional[str]
    base_url: str = "https://api.groq.com/openai/v1"

    @classmethod
    def from_env(cls) -> "GroqConfig":
        """Create configuration from environment variables."""
        return cls(api_key=os.getenv("GROQ_API_KEY"))

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
        """Create configuration from environment variables."""
        sender_name = os.getenv("SENDER_NAME", "Report Generator")
        sender_email = os.getenv("SENDER_EMAIL", "")
        
        recipients_to_str = os.getenv("REPORT_RECIPIENTS_TO", "")
        recipients_to = [r.strip() for r in recipients_to_str.split(",") if r.strip()]
        
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
        """Create configuration from environment variables."""
        return cls(
            provider=os.getenv("EMAIL_PROVIDER", "gmail"),
            username=os.getenv("EMAIL_USERNAME", ""),
            password=os.getenv("EMAIL_PASSWORD"),
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
        """Create all configurations from environment variables."""
        return cls(
            slack=SlackConfig.from_env(),
            groq=GroqConfig.from_env(),
            report=ReportConfig.from_env(),
            email=EmailConfig.from_env(),
            output_dir=os.getenv("REPORT_OUTPUT_DIR"),
        )
