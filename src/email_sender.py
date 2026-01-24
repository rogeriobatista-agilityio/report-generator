"""
Email sender for sending weekly reports to recipients.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class EmailConfig:
    """Email configuration."""
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    use_tls: bool = True


class EmailSender:
    """Send emails via SMTP."""

    # Common SMTP configurations
    SMTP_CONFIGS = {
        "gmail": {
            "server": "smtp.gmail.com",
            "port": 587,
            "use_tls": True,
        },
        "outlook": {
            "server": "smtp.office365.com",
            "port": 587,
            "use_tls": True,
        },
        "yahoo": {
            "server": "smtp.mail.yahoo.com",
            "port": 587,
            "use_tls": True,
        },
    }

    def __init__(self, config: EmailConfig):
        """Initialize the email sender."""
        self.config = config

    @classmethod
    def from_provider(cls, provider: str, username: str, password: str) -> "EmailSender":
        """
        Create an EmailSender for a known provider.
        
        Args:
            provider: One of 'gmail', 'outlook', 'yahoo'
            username: Email address
            password: App password (not regular password for Gmail/Outlook)
        """
        if provider not in cls.SMTP_CONFIGS:
            raise ValueError(f"Unknown provider: {provider}. Use one of: {list(cls.SMTP_CONFIGS.keys())}")
        
        smtp_config = cls.SMTP_CONFIGS[provider]
        config = EmailConfig(
            smtp_server=smtp_config["server"],
            smtp_port=smtp_config["port"],
            username=username,
            password=password,
            use_tls=smtp_config["use_tls"],
        )
        return cls(config)

    def send_report(
        self,
        subject: str,
        body: str,
        from_email: str,
        to_emails: list[str],
        cc_emails: list[str] = None,
        from_name: str = None,
    ) -> bool:
        """
        Send the weekly report via email.
        
        Args:
            subject: Email subject
            body: Email body (plain text)
            from_email: Sender email address
            to_emails: List of recipient email addresses
            cc_emails: List of CC email addresses
            from_name: Display name for sender
            
        Returns:
            True if email was sent successfully
        """
        if cc_emails is None:
            cc_emails = []

        # Create message
        msg = MIMEMultipart("alternative")
        
        # Set headers
        if from_name:
            msg["From"] = f"{from_name} <{from_email}>"
        else:
            msg["From"] = from_email
        
        msg["To"] = ", ".join(to_emails)
        if cc_emails:
            msg["Cc"] = ", ".join(cc_emails)
        msg["Subject"] = subject

        # Add plain text body
        text_part = MIMEText(body, "plain")
        msg.attach(text_part)

        # Also add HTML version for better formatting
        html_body = self._text_to_html(body)
        html_part = MIMEText(html_body, "html")
        msg.attach(html_part)

        # All recipients (to + cc)
        all_recipients = to_emails + cc_emails

        try:
            # Connect to SMTP server
            if self.config.use_tls:
                server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
                server.starttls(context=ssl.create_default_context())
            else:
                server = smtplib.SMTP_SSL(
                    self.config.smtp_server, 
                    self.config.smtp_port,
                    context=ssl.create_default_context()
                )

            # Login and send
            server.login(self.config.username, self.config.password)
            server.sendmail(from_email, all_recipients, msg.as_string())
            server.quit()
            
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"Authentication failed: {e}")
            print("\nFor Gmail, you need to use an App Password:")
            print("1. Go to https://myaccount.google.com/apppasswords")
            print("2. Generate a new app password for 'Mail'")
            print("3. Use that password instead of your regular password")
            return False
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    def _text_to_html(self, text: str) -> str:
        """Convert plain text report to HTML for better email formatting."""
        import html
        
        # Escape HTML characters
        escaped = html.escape(text)
        
        # Convert sections to bold
        lines = escaped.split("\n")
        html_lines = []
        
        for line in lines:
            # Make section headers bold
            if line.startswith("1. ") or line.startswith("2. ") or \
               line.startswith("3. ") or line.startswith("4. ") or \
               line.startswith("5. "):
                line = f"<strong>{line}</strong>"
            # Make category headers bold
            elif line.strip() in ["Feature Development", "Code & Infrastructure", 
                                  "Bug Fixes", "Documentation", "New Team Member Onboarding"]:
                line = f"<strong>{line}</strong>"
            # Convert bullet points
            elif line.strip().startswith("* ") or line.strip().startswith("- "):
                line = line.replace("* ", "• ", 1).replace("- ", "• ", 1)
            
            html_lines.append(line)
        
        # Join with <br> tags
        html_body = "<br>\n".join(html_lines)
        
        # Wrap in basic HTML
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: #333;
        }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""

    def test_connection(self) -> bool:
        """Test the SMTP connection."""
        try:
            if self.config.use_tls:
                server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
                server.starttls(context=ssl.create_default_context())
            else:
                server = smtplib.SMTP_SSL(
                    self.config.smtp_server,
                    self.config.smtp_port,
                    context=ssl.create_default_context()
                )
            
            server.login(self.config.username, self.config.password)
            server.quit()
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False


def send_report_email(
    report_file: str,
    from_email: str,
    from_name: str,
    to_emails: list[str],
    cc_emails: list[str],
    smtp_username: str,
    smtp_password: str,
    smtp_provider: str = "gmail",
    subject: str = None,
) -> bool:
    """
    Convenience function to send a report file via email.
    
    Args:
        report_file: Path to the report file
        from_email: Sender email
        from_name: Sender display name
        to_emails: List of recipient emails
        cc_emails: List of CC emails
        smtp_username: SMTP username (usually same as from_email)
        smtp_password: SMTP password or app password
        smtp_provider: 'gmail', 'outlook', or 'yahoo'
        subject: Email subject (auto-generated if not provided)
        
    Returns:
        True if sent successfully
    """
    # Read report file
    report_path = Path(report_file)
    if not report_path.exists():
        print(f"Report file not found: {report_file}")
        return False
    
    body = report_path.read_text()
    
    # Generate subject if not provided
    if subject is None:
        from datetime import datetime
        today = datetime.now()
        subject = f"End of Week Update - Week {today.isocalendar()[1]}, {today.year}"
    
    # Create sender and send
    sender = EmailSender.from_provider(smtp_provider, smtp_username, smtp_password)
    
    return sender.send_report(
        subject=subject,
        body=body,
        from_email=from_email,
        to_emails=to_emails,
        cc_emails=cc_emails,
        from_name=from_name,
    )
