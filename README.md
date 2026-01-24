# Slack Report Generator

A tool that reads daily status updates from a Slack channel and generates weekly summary reports. Available as both a CLI for technical users and a web UI for easy access.

## Features

- **Slack Integration**: Reads messages from any Slack channel using the Slack API
- **Thread Support**: Reads daily report threads with all replies
- **Smart Parsing**: Automatically identifies status update messages and extracts tasks
- **Weekly Aggregation**: Consolidates daily updates into a comprehensive weekly report
- **Categorized Output**: Groups tasks by category (Feature Development, Bug Fixes, Infrastructure, etc.)
- **Groq AI Enhancement** (Optional): Uses Groq AI to improve report quality and generate summary notes
- **Web UI**: Modern web interface for non-technical users
- **CLI**: Command-line interface for technical users
- **Email Sending**: Send generated reports directly via email
- **SQLite Database**: Manage recipients and settings through the UI

## Report Format

The generated report follows this structure:

```
1. NOTES
   - High-level summary and important updates

2. DONE
   Feature Development
   - V2-xxx: Task description - @Assignee
   
   Code & Infrastructure
   - Task description - PR #xxx - @Assignee

3. IN PROGRESS
   - V2-xxx: Current task - @Assignee

4. NEXT PLAN
   - Planned task for next week - @Assignee

5. QUESTIONS/BLOCKERS
   - Any blockers or questions that need attention
```

## Prerequisites

- Python 3.10+
- Node.js 18+ (for web UI)
- A Slack Bot Token with the following scopes:
  - `channels:history` - Read messages from channels
  - `channels:read` - Access channel information
  - `users:read` - Access user information
  - `groups:history` - Read messages from private channels (if needed)
  - `groups:read` - Access private channel information (if needed)
- (Optional) Groq API key from [Groq Console](https://console.groq.com/) for AI-enhanced reports

## Installation

1. Clone the repository:
   ```bash
   cd /path/to/report-generator
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

## Slack App Setup

1. Go to [Slack API Apps](https://api.slack.com/apps) and create a new app
2. Under "OAuth & Permissions", add the following Bot Token Scopes:
   - `channels:history`
   - `channels:read`
   - `users:read`
   - `groups:history` (for private channels)
   - `groups:read` (for private channels)
3. Install the app to your workspace
4. Copy the "Bot User OAuth Token" (starts with `xoxb-`)
5. Invite the bot to your status updates channel: `/invite @YourBotName`
6. Get the channel ID (right-click channel > View channel details > copy ID at bottom)

## Usage

### Web UI (Recommended for Non-Technical Users)

Start both the API and frontend:

```bash
# Terminal 1: Start the API
source venv/bin/activate
python -m uvicorn api.main:app --reload --port 8000

# Terminal 2: Start the frontend
cd web
npm install  # First time only
npm run dev
```

Then open http://localhost:3000 in your browser.

### CLI Commands

#### Generate Report for Current Week

```bash
python main.py generate
```

#### Generate Report for Specific Week

```bash
python main.py generate --week 3 --year 2026
```

#### Save Report to File

```bash
python main.py generate --output weekly_report.txt
```

#### Use AI Enhancement

```bash
python main.py generate --ai
```

#### Add Custom Notes

```bash
python main.py generate -n "New developer joined this week" -n "Holiday on Monday"
```

#### Test Slack Connection

```bash
python main.py test-connection
```

#### Preview Messages

```bash
python main.py preview --days 7
```

#### Send Report via Email

```bash
python main.py send reports/weekly_report_2026-01-23.txt
```

#### Test Email Configuration

```bash
python main.py test-email
```

## Configuration

Settings can be configured via the web UI (Settings page) or through environment variables:

| Environment Variable | Description | Required |
|---------------------|-------------|----------|
| `SLACK_BOT_TOKEN` | Slack Bot OAuth Token | Yes |
| `SLACK_CHANNEL_ID` | Channel ID to read messages from | Yes |
| `GROQ_API_KEY` | Groq AI API key for AI enhancement | No |
| `SENDER_NAME` | Name to use as report sender | No |
| `SENDER_EMAIL` | Email address of the sender | No |
| `REPORT_RECIPIENTS_TO` | Comma-separated TO recipients | No |
| `REPORT_RECIPIENTS_CC` | Comma-separated CC recipients | No |
| `EMAIL_PROVIDER` | Email provider (gmail, outlook, yahoo) | No |
| `EMAIL_USERNAME` | SMTP username | No |
| `EMAIL_PASSWORD` | SMTP password (app password for Gmail) | No |
| `REPORT_OUTPUT_DIR` | Directory for report output | No |

## Expected Message Format

The parser recognizes daily report threads with the header format:
```
Daily report - Jan 23, 2026
```

And status updates in threads that include sections like:

```
Done/Completed:
- Task 1 - @Person1
- Task 2 - @Person2

In Progress/Working on:
- V2-123: Current task - @Person1

Planned/Next:
- Task for tomorrow - @Person1

Blockers/Issues:
- Need clarification on X
```

The parser is flexible and can handle various formats including:
- Bullet points (-, *, •)
- Numbered lists
- Emoji markers (✅, 🔄, 📋, 🚫)
- Ticket IDs (V2-xxx, JIRA-xxx)
- PR references (PR #xxx, #xxx)
- @mentions

## Project Structure

```
report-generator/
├── main.py              # CLI entry point
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── .env                 # Your configuration (git-ignored)
├── README.md            # This file
├── api/
│   └── main.py          # FastAPI backend
├── web/                 # React frontend
│   ├── package.json
│   ├── src/
│   │   ├── App.jsx
│   │   └── components/
│   └── ...
├── data/                # SQLite database (git-ignored)
├── reports/             # Generated reports directory
├── templates/
│   └── sample_report.txt  # Report format template
└── src/
    ├── __init__.py      # Package initialization
    ├── __main__.py      # Module entry point
    ├── cli.py           # Command-line interface
    ├── config.py        # Configuration management
    ├── database.py      # SQLite database management
    ├── slack_client.py  # Slack API client
    ├── message_parser.py    # Message parsing logic
    ├── report_generator.py  # Report generation with AI
    └── email_sender.py  # Email sending functionality
```

## Troubleshooting

### "SLACK_BOT_TOKEN environment variable is required"
Make sure you've created a `.env` file from `.env.example` and added your Slack token, or configure it via the web UI Settings page.

### "channel_not_found" error
1. Ensure the channel ID is correct
2. Make sure the bot has been invited to the channel
3. For private channels, add `groups:history` and `groups:read` scopes and invite the bot

### No status updates found
The parser looks for daily report threads with the format "Daily report - Month Day, Year". Ensure your team posts daily reports in this format with status updates as thread replies.

### Groq AI enhancement not working
1. Check that `GROQ_API_KEY` is set (via UI or `.env` file)
2. Get your API key from [Groq Console](https://console.groq.com/)
3. Verify your API key is valid

### Email sending fails
1. For Gmail, you must use an App Password (not your regular password)
2. Enable 2FA on your Google account
3. Create an App Password at https://myaccount.google.com/apppasswords

## License

MIT License - feel free to use and modify as needed.
