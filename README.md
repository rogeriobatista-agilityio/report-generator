# Automated Slack Report Generator

An automated agent that reads daily status updates from a Slack channel and generates weekly summary reports every Friday at 8 PM Brazil Time.

## Features

- **Slack Integration**: Reads messages from any Slack channel using the Slack API
- **Smart Parsing**: Automatically identifies status update messages and extracts tasks
- **Weekly Aggregation**: Consolidates daily updates into a comprehensive weekly report
- **Categorized Output**: Groups tasks by category (Feature Development, Bug Fixes, Infrastructure, etc.)
- **Grok AI Enhancement** (Optional): Uses xAI's Grok to improve report quality and generate summary notes
- **Flexible Output**: Print to console or save to file
- **Automated Scheduling**: Configured to run every Friday at 8 PM BRT via launchd

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
- A Slack Bot Token with the following scopes:
  - `channels:history` - Read messages from channels
  - `channels:read` - Access channel information
  - `users:read` - Access user information
- (Optional) Grok API key from [xAI Console](https://console.x.ai/) for AI-enhanced reports

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
3. Install the app to your workspace
4. Copy the "Bot User OAuth Token" (starts with `xoxb-`)
5. Invite the bot to your status updates channel: `/invite @YourBotName`
6. Get the channel ID (right-click channel > View channel details > copy ID at bottom)

## Usage

### Generate Report for Current Week

```bash
python main.py generate
```

### Generate Report for Specific Week

```bash
python main.py generate --week 3 --year 2026
```

### Save Report to File

```bash
python main.py generate --output weekly_report.txt
```

### Use AI Enhancement

```bash
python main.py generate --ai
```

### Add Custom Notes

```bash
python main.py generate -n "New developer joined this week" -n "Holiday on Monday"
```

### Test Slack Connection

```bash
python main.py test-connection
```

### Preview Messages

```bash
python main.py preview --days 7
```

### View Scheduling Information

```bash
python main.py schedule-info
```

## Scheduling (Every Friday at 8 PM Brazil Time)

The report generator is already configured to run automatically via launchd on macOS.

### Verify the Schedule

```bash
# Check if the agent is loaded
launchctl list | grep report-generator

# View the schedule
cat ~/Library/LaunchAgents/com.agilityio.report-generator.plist
```

### Manual Control

```bash
# Unload the scheduled job
launchctl unload ~/Library/LaunchAgents/com.agilityio.report-generator.plist

# Reload the scheduled job
launchctl load ~/Library/LaunchAgents/com.agilityio.report-generator.plist

# Run immediately (for testing)
./scripts/run_report.sh
```

### Using Cron (Alternative)

If you prefer cron over launchd:

```bash
# Run every Friday at 8 PM (Brazil Time)
0 20 * * 5 /Users/rogeriobatista/Projects/AgilityIO/report-generator/scripts/run_report.sh
```

## Configuration

| Environment Variable | Description | Required |
|---------------------|-------------|----------|
| `SLACK_BOT_TOKEN` | Slack Bot OAuth Token | Yes |
| `SLACK_CHANNEL_ID` | Channel ID to read messages from | Yes |
| `GROK_API_KEY` | Grok AI API key from xAI for AI enhancement | No |
| `REPORT_RECIPIENTS` | Comma-separated list of recipients for header | No |
| `SENDER_NAME` | Name to use as report sender | No |
| `REPORT_OUTPUT_DIR` | Directory for scheduled report output | No |

## Expected Message Format

The parser recognizes status updates that include sections like:

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
├── main.py              # Main entry point
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── .env                 # Your configuration (git-ignored)
├── README.md            # This file
├── scripts/
│   └── run_report.sh    # Automated runner script
├── reports/             # Generated reports directory
├── logs/                # Log files
├── templates/
│   └── sample_report.txt  # Report format template
└── src/
    ├── __init__.py      # Package initialization
    ├── __main__.py      # Module entry point
    ├── cli.py           # Command-line interface
    ├── config.py        # Configuration management
    ├── slack_client.py  # Slack API client
    ├── message_parser.py    # Message parsing logic
    └── report_generator.py  # Report generation with Grok AI
```

## Troubleshooting

### "SLACK_BOT_TOKEN environment variable is required"
Make sure you've created a `.env` file from `.env.example` and added your Slack token.

### "channel_not_found" error
1. Ensure the channel ID is correct
2. Make sure the bot has been invited to the channel
3. For private channels, the bot needs to be explicitly invited

### No status updates found
The parser looks for messages containing typical status update patterns. Ensure your team's messages include:
- Section headers (Done, In Progress, etc.)
- Bullet points or numbered lists
- Sufficient length (> 100 characters)

### Grok AI enhancement not working
1. Check that `GROK_API_KEY` is set in your `.env` file
2. Ensure you have the `openai` package installed (Grok uses OpenAI-compatible API)
3. Get your API key from [xAI Console](https://console.x.ai/)
4. Verify your API key has available credits

## License

MIT License - feel free to use and modify as needed.
