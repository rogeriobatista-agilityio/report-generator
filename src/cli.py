"""
Command-line interface for the report generator.
"""

import click
from datetime import datetime, timedelta
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import AppConfig
from .slack_client import SlackClient
from .message_parser import MessageParser
from .report_generator import ReportGenerator, GroqReportEnhancer


console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    Automated Slack Report Generator
    
    Read daily status updates from Slack and generate weekly summary reports.
    """
    pass


@cli.command()
@click.option(
    "--week",
    type=int,
    default=None,
    help="ISO week number to generate report for (default: current week)",
)
@click.option(
    "--year",
    type=int,
    default=None,
    help="Year for the report (default: current year)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output file path (default: print to console)",
)
@click.option(
    "--ai/--no-ai",
    default=False,
    help="Use Groq AI enhancement for the report (requires GROQ_API_KEY)",
)
@click.option(
    "--notes",
    "-n",
    multiple=True,
    help="Additional notes to include in the report (can be used multiple times)",
)
def generate(week: int, year: int, output: str, ai: bool, notes: tuple):
    """Generate a weekly status report from Slack messages."""
    
    try:
        config = AppConfig.from_env()
    except ValueError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        console.print("\nPlease copy .env.example to .env and configure your credentials.")
        raise click.Abort()

    # Determine the week to report on
    now = datetime.now()
    if year is None:
        year = now.year
    if week is None:
        week = now.isocalendar()[1]

    console.print(Panel(
        f"Generating report for Week {week}, {year}",
        title="📊 Report Generator",
        border_style="blue"
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Fetch messages from Slack
        task = progress.add_task("Connecting to Slack...", total=None)
        slack_client = SlackClient(config.slack)
        
        progress.update(task, description="Fetching daily report threads from Slack...")
        
        # Get status updates from daily report threads
        status_messages, daily_reports = slack_client.get_weekly_status_updates(year, week)
        
        console.print(f"\n✓ Found [green]{len(daily_reports)}[/green] daily report threads")
        console.print(f"✓ Found [green]{len(status_messages)}[/green] status update messages")

        if not status_messages:
            console.print("[yellow]No status updates found in daily report threads.[/yellow]")
            console.print("Make sure daily reports are posted with 'Daily report' in the message,")
            console.print("and team members reply with their status updates in the thread.")
            return

        # Parse status updates
        progress.update(task, description="Parsing status updates...")
        parser = MessageParser()
        statuses = parser.parse_messages(status_messages)
        
        console.print(f"✓ Parsed [green]{len(statuses)}[/green] structured status updates")

        # Generate report
        progress.update(task, description="Generating report...")
        generator = ReportGenerator(
            sender_name=config.report.sender_name,
            sender_email=config.report.sender_email,
            recipients_to=config.report.recipients_to,
            recipients_cc=config.report.recipients_cc,
        )
        
        # Use Groq AI enhancement if requested
        if ai and config.groq.is_available:
            progress.update(task, description="Enhancing report with Groq AI...")
            enhancer = GroqReportEnhancer(config.groq.api_key)
            raw_texts = [msg.text for msg in status_messages]
            
            # Calculate date range from daily reports
            if daily_reports:
                dates = [r['date'] for r in daily_reports]
                start_date = min(dates)
                end_date = max(dates)
                date_range = f"{start_date.strftime('%B %d')} to {end_date.strftime('%B %d, %Y')}"
            else:
                date_range = f"Week {week}, {year}"
            
            enhanced = enhancer.enhance_report(
                raw_texts, 
                date_range=date_range,
                sender_name=config.report.sender_name
            )
            
            if enhanced:
                report = enhanced
            else:
                console.print("[yellow]Groq AI enhancement failed, using standard report.[/yellow]")
                report = generator.generate(statuses, list(notes))
        else:
            report = generator.generate(statuses, list(notes))

        progress.update(task, description="Done!")

    # Output the report
    if output:
        output_path = Path(output)
        output_path.write_text(report)
        console.print(f"\n✓ Report saved to [green]{output_path}[/green]")
    else:
        console.print("\n")
        console.print(Panel(report, title="📋 Weekly Report", border_style="green"))

    # Show summary
    console.print("\n[bold]Report Summary:[/bold]")
    console.print(f"  • Daily report threads: {len(daily_reports)}")
    console.print(f"  • Status messages: {len(status_messages)}")
    console.print(f"  • Team members: {len(set(s.author for s in statuses))}")


@cli.command()
def test_connection():
    """Test the Slack connection and list available channels."""
    
    try:
        config = AppConfig.from_env()
    except ValueError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        raise click.Abort()

    console.print("Testing Slack connection...")
    
    try:
        from slack_sdk import WebClient
        client = WebClient(token=config.slack.bot_token)
        
        # Test auth
        auth_response = client.auth_test()
        console.print(f"✓ Connected as: [green]{auth_response['user']}[/green]")
        console.print(f"✓ Team: [green]{auth_response['team']}[/green]")
        
        # Test channel access
        channel_response = client.conversations_info(channel=config.slack.channel_id)
        channel_name = channel_response["channel"]["name"]
        console.print(f"✓ Channel: [green]#{channel_name}[/green]")
        
        console.print("\n[green]All tests passed![/green]")
        
    except Exception as e:
        console.print(f"[red]Connection failed:[/red] {e}")
        raise click.Abort()


@cli.command()
@click.option(
    "--days",
    type=int,
    default=7,
    help="Number of days to look back (default: 7)",
)
def preview(days: int):
    """Preview daily report threads that would be included in the report."""
    
    try:
        config = AppConfig.from_env()
    except ValueError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        raise click.Abort()

    console.print(f"Fetching daily report threads from the last {days} days...")
    
    slack_client = SlackClient(config.slack)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Find daily report threads
    daily_reports = slack_client.find_daily_report_threads(start_date, end_date)
    
    if not daily_reports:
        console.print("\n[yellow]No daily report threads found.[/yellow]")
        console.print("Looking for messages containing 'Daily report', 'status update', or 'standup'...")
        
        # Show all messages for debugging
        console.print("\n[dim]All messages in date range:[/dim]")
        messages = slack_client.get_channel_messages(start_date, end_date)
        for msg in messages[:20]:  # Show first 20
            text_preview = msg.text[:100] + "..." if len(msg.text) > 100 else msg.text
            text_preview = text_preview.replace("\n", " ")
            console.print(f"  • {msg.user_name}: {text_preview}")
        return
    
    console.print(f"\nFound [green]{len(daily_reports)}[/green] daily report threads\n")
    
    total_updates = 0
    for report in daily_reports:
        header = report['header']
        replies = report['replies']
        
        # Show header
        console.print(Panel(
            f"[bold]{header.text}[/bold]\n\n"
            f"Posted by: {header.user_name}\n"
            f"Date: {header.timestamp.strftime('%Y-%m-%d %H:%M')}\n"
            f"Thread replies: {len(replies)}",
            title=f"📋 Daily Report - {header.timestamp.strftime('%B %d, %Y')}",
            border_style="blue"
        ))
        
        # Show thread replies (status updates)
        if replies:
            console.print("  [bold]Status Updates:[/bold]")
            for reply in replies:
                text_preview = reply.text[:150] + "..." if len(reply.text) > 150 else reply.text
                text_preview = text_preview.replace("\n", " | ")
                console.print(f"    • [green]{reply.user_name}[/green]: {text_preview}")
                total_updates += 1
        else:
            console.print("  [dim]No thread replies found[/dim]")
        
        console.print("")
    
    console.print(f"[bold]Total status updates found: {total_updates}[/bold]")


@cli.command()
@click.argument("template_file", type=click.Path(exists=True))
def from_template(template_file: str):
    """Generate a report using a custom template file."""
    
    template = Path(template_file).read_text()
    console.print(f"Loaded template from: {template_file}")
    console.print("\n[yellow]Custom template support coming soon![/yellow]")


@cli.command()
def schedule_info():
    """Show information about scheduling the report generator."""
    
    info = """
# Scheduling the Report Generator

## Using Cron (macOS/Linux)

To run the report generator every Friday at 5 PM:

```bash
0 17 * * 5 cd /path/to/report-generator && python -m src.cli generate --output /path/to/reports/report_$(date +\\%Y-\\%m-\\%d).txt
```

## Using launchd (macOS)

Create a plist file at `~/Library/LaunchAgents/com.report-generator.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.report-generator</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>-m</string>
        <string>src.cli</string>
        <string>generate</string>
        <string>--output</string>
        <string>/path/to/report.txt</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/report-generator</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>5</integer>
        <key>Hour</key>
        <integer>17</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
```

Then load it:
```bash
launchctl load ~/Library/LaunchAgents/com.report-generator.plist
```

## Using Task Scheduler (Windows)

Use Task Scheduler to create a task that runs every Friday at 5 PM,
executing: `python -m src.cli generate --output C:\\path\\to\\report.txt`
"""
    
    console.print(Markdown(info))


@cli.command()
@click.argument("report_file", type=click.Path(exists=True))
@click.option(
    "--subject",
    "-s",
    default=None,
    help="Email subject (auto-generated if not provided)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be sent without actually sending",
)
def send(report_file: str, subject: str, dry_run: bool):
    """Send a generated report via email to configured recipients."""
    
    try:
        config = AppConfig.from_env()
    except ValueError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        raise click.Abort()

    # Check email configuration
    if not config.email.is_available:
        console.print("[red]Email not configured.[/red]")
        console.print("\nPlease add these to your .env file:")
        console.print("  EMAIL_PROVIDER=gmail")
        console.print("  EMAIL_USERNAME=your-email@gmail.com")
        console.print("  EMAIL_PASSWORD=your-app-password")
        console.print("\nFor Gmail, use an App Password: https://myaccount.google.com/apppasswords")
        raise click.Abort()

    # Check recipients
    if not config.report.recipients_to:
        console.print("[red]No recipients configured.[/red]")
        console.print("Please set REPORT_RECIPIENTS_TO in your .env file.")
        raise click.Abort()

    # Read report file
    report_path = Path(report_file)
    report_content = report_path.read_text()

    # Generate subject if not provided
    if subject is None:
        now = datetime.now()
        subject = f"End of Week Update - Week {now.isocalendar()[1]}, {now.year}"

    # Extract email addresses (remove display names like "Name <email>")
    import re
    def extract_email(recipient: str) -> str:
        match = re.search(r'<([^>]+)>', recipient)
        return match.group(1) if match else recipient.strip()

    to_emails = [extract_email(r) for r in config.report.recipients_to]
    cc_emails = [extract_email(r) for r in config.report.recipients_cc]

    # Show preview
    console.print(Panel(
        f"[bold]From:[/bold] {config.report.sender_name} <{config.report.sender_email}>\n"
        f"[bold]To:[/bold] {', '.join(to_emails)}\n"
        f"[bold]CC:[/bold] {', '.join(cc_emails) if cc_emails else '(none)'}\n"
        f"[bold]Subject:[/bold] {subject}\n"
        f"[bold]File:[/bold] {report_file}",
        title="📧 Email Preview",
        border_style="blue"
    ))

    # Show report preview
    preview_lines = report_content.split('\n')[:15]
    console.print("\n[dim]Report preview (first 15 lines):[/dim]")
    for line in preview_lines:
        console.print(f"  {line}")
    console.print("  ...")

    if dry_run:
        console.print("\n[yellow]Dry run - email not sent.[/yellow]")
        return

    # Confirm before sending
    if not click.confirm("\nSend this email?"):
        console.print("[yellow]Cancelled.[/yellow]")
        return

    # Send email
    console.print("\nSending email...")
    
    from .email_sender import EmailSender
    
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
            console.print("[green]✓ Email sent successfully![/green]")
        else:
            console.print("[red]✗ Failed to send email.[/red]")
            raise click.Abort()
            
    except Exception as e:
        console.print(f"[red]Error sending email:[/red] {e}")
        raise click.Abort()


@cli.command()
def test_email():
    """Test email configuration by sending a test email to yourself."""
    
    try:
        config = AppConfig.from_env()
    except ValueError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        raise click.Abort()

    if not config.email.is_available:
        console.print("[red]Email not configured.[/red]")
        console.print("\nPlease add EMAIL_USERNAME and EMAIL_PASSWORD to your .env file.")
        raise click.Abort()

    console.print("Testing email configuration...")
    console.print(f"  Provider: {config.email.provider}")
    console.print(f"  Username: {config.email.username}")
    
    from .email_sender import EmailSender
    
    try:
        sender = EmailSender.from_provider(
            config.email.provider,
            config.email.username,
            config.email.password,
        )
        
        # Test connection
        console.print("\nTesting SMTP connection...")
        if sender.test_connection():
            console.print("[green]✓ SMTP connection successful![/green]")
        else:
            console.print("[red]✗ SMTP connection failed.[/red]")
            raise click.Abort()
        
        # Send test email
        if click.confirm("\nSend a test email to yourself?"):
            success = sender.send_report(
                subject="Test Email from Report Generator",
                body="This is a test email from the Report Generator.\n\nIf you received this, your email configuration is working correctly!",
                from_email=config.email.username,
                to_emails=[config.email.username],
                cc_emails=[],
                from_name="Report Generator Test",
            )
            
            if success:
                console.print(f"[green]✓ Test email sent to {config.email.username}[/green]")
            else:
                console.print("[red]✗ Failed to send test email.[/red]")
                
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
