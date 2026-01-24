"""
FastAPI backend for the Report Generator.
Provides REST API endpoints for the web UI.
"""

import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import AppConfig
from src.slack_client import SlackClient
from src.message_parser import MessageParser
from src.report_generator import ReportGenerator, GroqReportEnhancer
from src.email_sender import EmailSender
from src.database import SettingsManager, RecipientsManager, ReportHistoryManager, init_database

# Initialize database
init_database()

app = FastAPI(
    title="Report Generator API",
    description="API for generating and sending weekly status reports",
    version="1.0.0",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class GenerateReportRequest(BaseModel):
    week: Optional[int] = None
    year: Optional[int] = None
    use_ai: bool = True
    notes: list[str] = []


class GenerateReportResponse(BaseModel):
    success: bool
    report: Optional[str] = None
    filename: Optional[str] = None
    date_range: Optional[str] = None
    stats: Optional[dict] = None
    error: Optional[str] = None


class SendEmailRequest(BaseModel):
    report_file: str
    subject: Optional[str] = None
    to_emails: Optional[list[str]] = None
    cc_emails: Optional[list[str]] = None


class SendEmailResponse(BaseModel):
    success: bool
    message: str


class PreviewResponse(BaseModel):
    daily_reports: list[dict]
    total_updates: int
    date_range: Optional[str] = None


class ConfigResponse(BaseModel):
    slack_configured: bool
    ai_configured: bool
    email_configured: bool
    sender_name: str
    sender_email: str
    recipients_to: list[str]
    recipients_cc: list[str]


class ReportFile(BaseModel):
    name: str
    path: str
    created: str
    size: int


# Recipient models
class RecipientCreate(BaseModel):
    email: str
    name: Optional[str] = None
    type: str = "to"  # "to" or "cc"


class RecipientUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    active: Optional[bool] = None


class RecipientResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    type: str
    active: bool


# Settings models
class SettingUpdate(BaseModel):
    value: str
    description: Optional[str] = None


# Helper function to get config
def get_config() -> AppConfig:
    try:
        return AppConfig.from_env()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Report Generator API is running"}


@app.get("/api/config", response_model=ConfigResponse)
async def get_configuration():
    """Get current configuration status."""
    config = get_config()
    
    # Try to get recipients from database first, fallback to .env
    db_recipients_to = RecipientsManager.get_email_list("to")
    db_recipients_cc = RecipientsManager.get_email_list("cc")
    
    recipients_to = db_recipients_to if db_recipients_to else config.report.recipients_to
    recipients_cc = db_recipients_cc if db_recipients_cc else config.report.recipients_cc
    
    return ConfigResponse(
        slack_configured=bool(config.slack.bot_token and config.slack.channel_id),
        ai_configured=config.groq.is_available,
        email_configured=config.email.is_available,
        sender_name=config.report.sender_name,
        sender_email=config.report.sender_email,
        recipients_to=recipients_to,
        recipients_cc=recipients_cc,
    )


@app.get("/api/preview")
async def preview_messages(days: int = 7):
    """Preview daily report threads from the last N days."""
    config = get_config()
    
    try:
        slack_client = SlackClient(config.slack)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        daily_reports = slack_client.find_daily_report_threads(start_date, end_date)
        
        # Format for response
        reports_data = []
        total_updates = 0
        
        for report in daily_reports:
            header = report['header']
            replies = report['replies']
            total_updates += len(replies)
            
            reports_data.append({
                'date': report['date'].isoformat(),
                'header_text': header.text[:200],
                'posted_by': header.user_name,
                'reply_count': len(replies),
                'replies': [
                    {
                        'user': r.user_name,
                        'text': r.text[:500],
                        'timestamp': r.timestamp.isoformat(),
                    }
                    for r in replies[:5]  # Limit to first 5 replies
                ]
            })
        
        # Calculate date range
        date_range = None
        if daily_reports:
            dates = [r['date'] for r in daily_reports]
            start = min(dates)
            end = max(dates)
            date_range = f"{start.strftime('%B %d')} to {end.strftime('%B %d, %Y')}"
        
        return PreviewResponse(
            daily_reports=reports_data,
            total_updates=total_updates,
            date_range=date_range,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate", response_model=GenerateReportResponse)
async def generate_report(request: GenerateReportRequest):
    """Generate a weekly report."""
    config = get_config()
    
    try:
        slack_client = SlackClient(config.slack)
        
        # Determine week
        now = datetime.now()
        year = request.year or now.year
        week = request.week or now.isocalendar()[1]
        
        # Get status updates from daily report threads
        status_messages, daily_reports = slack_client.get_weekly_status_updates(year, week)
        
        if not status_messages:
            return GenerateReportResponse(
                success=False,
                error="No status updates found in daily report threads for this week.",
            )
        
        # Calculate date range
        if daily_reports:
            dates = [r['date'] for r in daily_reports]
            start_date = min(dates)
            end_date = max(dates)
            date_range = f"{start_date.strftime('%B %d')} to {end_date.strftime('%B %d, %Y')}"
        else:
            date_range = f"Week {week}, {year}"
        
        # Parse status updates
        parser = MessageParser()
        statuses = parser.parse_messages(status_messages)
        
        # Generate report
        generator = ReportGenerator(
            sender_name=config.report.sender_name,
            sender_email=config.report.sender_email,
            recipients_to=config.report.recipients_to,
            recipients_cc=config.report.recipients_cc,
        )
        
        # Use AI enhancement if requested and available
        report = None
        if request.use_ai and config.groq.is_available:
            enhancer = GroqReportEnhancer(config.groq.api_key)
            raw_texts = [msg.text for msg in status_messages]
            report = enhancer.enhance_report(
                raw_texts,
                date_range=date_range,
                sender_name=config.report.sender_name
            )
        
        if not report:
            report = generator.generate(statuses, request.notes)
        
        # Save report to file
        reports_dir = Path(config.output_dir or "reports")
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"weekly_report_{timestamp}.txt"
        filepath = reports_dir / filename
        filepath.write_text(report)
        
        return GenerateReportResponse(
            success=True,
            report=report,
            filename=filename,
            date_range=date_range,
            stats={
                "daily_reports": len(daily_reports),
                "status_messages": len(status_messages),
                "parsed_statuses": len(statuses),
            }
        )
        
    except Exception as e:
        return GenerateReportResponse(
            success=False,
            error=str(e),
        )


@app.get("/api/reports", response_model=list[ReportFile])
async def list_reports():
    """List all generated report files."""
    config = get_config()
    reports_dir = Path(config.output_dir or "reports")
    
    if not reports_dir.exists():
        return []
    
    files = []
    for f in sorted(reports_dir.glob("*.txt"), key=lambda x: x.stat().st_mtime, reverse=True):
        stat = f.stat()
        files.append(ReportFile(
            name=f.name,
            path=str(f),
            created=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            size=stat.st_size,
        ))
    
    return files


@app.get("/api/reports/{filename}")
async def get_report(filename: str):
    """Get content of a specific report file."""
    config = get_config()
    reports_dir = Path(config.output_dir or "reports")
    filepath = reports_dir / filename
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    content = filepath.read_text()
    return {"filename": filename, "content": content}


@app.delete("/api/reports/{filename}")
async def delete_report(filename: str):
    """Delete a report file."""
    config = get_config()
    reports_dir = Path(config.output_dir or "reports")
    filepath = reports_dir / filename
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    filepath.unlink()
    return {"success": True, "message": f"Deleted {filename}"}


@app.post("/api/send-email", response_model=SendEmailResponse)
async def send_email(request: SendEmailRequest):
    """Send a report via email."""
    config = get_config()
    
    if not config.email.is_available:
        raise HTTPException(
            status_code=400,
            detail="Email not configured. Please set EMAIL_USERNAME and EMAIL_PASSWORD in .env"
        )
    
    # Find report file
    reports_dir = Path(config.output_dir or "reports")
    filepath = reports_dir / request.report_file
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    
    report_content = filepath.read_text()
    
    # Generate subject if not provided
    subject = request.subject
    if not subject:
        now = datetime.now()
        subject = f"End of Week Update - Week {now.isocalendar()[1]}, {now.year}"
    
    # Extract email addresses
    def extract_email(recipient: str) -> str:
        match = re.search(r'<([^>]+)>', recipient)
        return match.group(1) if match else recipient.strip()
    
    to_emails = request.to_emails or [extract_email(r) for r in config.report.recipients_to]
    cc_emails = request.cc_emails or [extract_email(r) for r in config.report.recipients_cc]
    
    try:
        sender = EmailSender.from_provider(
            config.email.provider,
            config.email.username,
            config.email.password,
        )
        
        success = sender.send_report(
            subject=subject,
            body=report_content,
            from_email=config.report.sender_email,
            to_emails=to_emails,
            cc_emails=cc_emails,
            from_name=config.report.sender_name,
        )
        
        if success:
            return SendEmailResponse(
                success=True,
                message=f"Email sent successfully to {', '.join(to_emails)}"
            )
        else:
            return SendEmailResponse(
                success=False,
                message="Failed to send email. Check your email configuration."
            )
            
    except Exception as e:
        return SendEmailResponse(
            success=False,
            message=str(e)
        )


@app.post("/api/test-email")
async def test_email_config():
    """Test email configuration."""
    config = get_config()
    
    if not config.email.is_available:
        return {"success": False, "message": "Email not configured"}
    
    try:
        sender = EmailSender.from_provider(
            config.email.provider,
            config.email.username,
            config.email.password,
        )
        
        if sender.test_connection():
            return {"success": True, "message": "SMTP connection successful"}
        else:
            return {"success": False, "message": "SMTP connection failed"}
            
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.post("/api/test-slack")
async def test_slack_config():
    """Test Slack configuration."""
    config = get_config()
    
    try:
        from slack_sdk import WebClient
        client = WebClient(token=config.slack.bot_token)
        
        auth_response = client.auth_test()
        channel_response = client.conversations_info(channel=config.slack.channel_id)
        
        return {
            "success": True,
            "bot_name": auth_response.get("user"),
            "team": auth_response.get("team"),
            "channel": channel_response["channel"]["name"],
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


# =============================================================================
# Recipients Management Endpoints
# =============================================================================

@app.get("/api/recipients")
async def list_recipients(active_only: bool = False):
    """List all recipients."""
    recipients = RecipientsManager.get_all(active_only=active_only)
    return {"recipients": recipients}


@app.post("/api/recipients")
async def create_recipient(recipient: RecipientCreate):
    """Add a new recipient."""
    recipient_id = RecipientsManager.add(
        email=recipient.email,
        name=recipient.name,
        recipient_type=recipient.type,
    )
    return {"success": True, "id": recipient_id, "message": f"Recipient {recipient.email} added"}


@app.put("/api/recipients/{recipient_id}")
async def update_recipient(recipient_id: int, recipient: RecipientUpdate):
    """Update a recipient."""
    RecipientsManager.update(
        recipient_id=recipient_id,
        email=recipient.email,
        name=recipient.name,
        recipient_type=recipient.type,
        active=recipient.active,
    )
    return {"success": True, "message": "Recipient updated"}


@app.delete("/api/recipients/{recipient_id}")
async def delete_recipient(recipient_id: int):
    """Delete a recipient."""
    RecipientsManager.delete(recipient_id)
    return {"success": True, "message": "Recipient deleted"}


# =============================================================================
# Settings Management Endpoints
# =============================================================================

@app.get("/api/settings")
async def get_settings():
    """Get all settings (sensitive values masked)."""
    settings = SettingsManager.get_all()
    # Mask sensitive values
    masked = {}
    sensitive_keys = ["email_password", "slack_bot_token", "groq_api_key"]
    for key, value in settings.items():
        if key in sensitive_keys and value:
            masked[key] = "***" + value[-4:] if len(value) > 4 else "****"
        else:
            masked[key] = value
    return {"settings": masked}


@app.get("/api/settings/raw")
async def get_settings_raw():
    """Get all settings with actual values (for editing)."""
    settings = SettingsManager.get_all()
    return {"settings": settings}


@app.get("/api/settings/{key}")
async def get_setting(key: str):
    """Get a specific setting."""
    value = SettingsManager.get(key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    return {"key": key, "value": value}


@app.put("/api/settings/{key}")
async def update_setting(key: str, setting: SettingUpdate):
    """Update a setting."""
    SettingsManager.set(key, setting.value, setting.description)
    return {"success": True, "message": f"Setting '{key}' updated"}


@app.delete("/api/settings/{key}")
async def delete_setting(key: str):
    """Delete a setting (reset to default)."""
    SettingsManager.delete(key)
    return {"success": True, "message": f"Setting '{key}' deleted"}


@app.post("/api/settings/import-env")
async def import_settings_from_env(force: bool = True):
    """Import settings from .env file to database.
    
    Args:
        force: If True, overwrite existing settings and recipients.
    """
    try:
        SettingsManager.initialize_from_env()
        recipient_count = RecipientsManager.initialize_from_env(force=force)
        return {
            "success": True, 
            "message": f"Settings imported from .env file. {recipient_count} recipients imported."
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


# =============================================================================
# Report History Endpoints
# =============================================================================

@app.get("/api/history")
async def get_report_history(limit: int = 20):
    """Get report generation history."""
    history = ReportHistoryManager.get_recent(limit)
    return {"history": history}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
