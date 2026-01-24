"""
Slack client for reading channel messages and user information.
"""

from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .config import SlackConfig


@dataclass
class SlackMessage:
    """Represents a Slack message."""
    user_id: str
    user_name: str
    text: str
    timestamp: datetime
    thread_ts: Optional[str] = None
    reactions: list[dict] = None

    def __post_init__(self):
        if self.reactions is None:
            self.reactions = []


@dataclass
class SlackUser:
    """Represents a Slack user."""
    id: str
    name: str
    real_name: str
    display_name: str


class SlackClient:
    """Client for interacting with Slack API."""

    def __init__(self, config: SlackConfig):
        """Initialize the Slack client."""
        self.config = config
        self.client = WebClient(token=config.bot_token)
        self._user_cache: dict[str, SlackUser] = {}

    def get_user(self, user_id: str) -> SlackUser:
        """Get user information by ID, with caching."""
        if user_id in self._user_cache:
            return self._user_cache[user_id]

        try:
            response = self.client.users_info(user=user_id)
            user_data = response["user"]
            user = SlackUser(
                id=user_id,
                name=user_data.get("name", "unknown"),
                real_name=user_data.get("real_name", "Unknown User"),
                display_name=user_data.get("profile", {}).get("display_name", ""),
            )
            self._user_cache[user_id] = user
            return user
        except SlackApiError as e:
            print(f"Error fetching user {user_id}: {e}")
            return SlackUser(
                id=user_id,
                name="unknown",
                real_name="Unknown User",
                display_name="",
            )

    def get_channel_messages(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000,
    ) -> list[SlackMessage]:
        """
        Fetch messages from the configured channel within a date range.
        
        Args:
            start_date: Start of the date range (inclusive)
            end_date: End of the date range (inclusive)
            limit: Maximum number of messages to fetch
            
        Returns:
            List of SlackMessage objects sorted by timestamp
        """
        messages = []
        
        # Convert dates to Unix timestamps
        oldest = start_date.timestamp()
        latest = end_date.timestamp()

        try:
            cursor = None
            while True:
                response = self.client.conversations_history(
                    channel=self.config.channel_id,
                    oldest=str(oldest),
                    latest=str(latest),
                    limit=min(limit - len(messages), 200),
                    cursor=cursor,
                )

                for msg in response.get("messages", []):
                    # Skip bot messages and system messages
                    if msg.get("subtype") in ["bot_message", "channel_join", "channel_leave"]:
                        continue
                    
                    user_id = msg.get("user", "")
                    if not user_id:
                        continue

                    user = self.get_user(user_id)
                    
                    # Parse timestamp
                    ts = float(msg.get("ts", 0))
                    timestamp = datetime.fromtimestamp(ts)

                    messages.append(SlackMessage(
                        user_id=user_id,
                        user_name=user.real_name or user.display_name or user.name,
                        text=msg.get("text", ""),
                        timestamp=timestamp,
                        thread_ts=msg.get("thread_ts"),
                        reactions=msg.get("reactions", []),
                    ))

                # Check for pagination
                if not response.get("has_more") or len(messages) >= limit:
                    break
                    
                cursor = response.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break

        except SlackApiError as e:
            print(f"Error fetching messages: {e}")
            raise

        # Sort messages by timestamp (oldest first)
        messages.sort(key=lambda m: m.timestamp)
        return messages

    def get_thread_messages(self, thread_ts: str) -> list[SlackMessage]:
        """Fetch all messages in a thread."""
        messages = []

        try:
            response = self.client.conversations_replies(
                channel=self.config.channel_id,
                ts=thread_ts,
            )

            for msg in response.get("messages", []):
                user_id = msg.get("user", "")
                if not user_id:
                    continue

                user = self.get_user(user_id)
                ts = float(msg.get("ts", 0))
                timestamp = datetime.fromtimestamp(ts)

                messages.append(SlackMessage(
                    user_id=user_id,
                    user_name=user.real_name or user.display_name or user.name,
                    text=msg.get("text", ""),
                    timestamp=timestamp,
                    thread_ts=msg.get("thread_ts"),
                    reactions=msg.get("reactions", []),
                ))

        except SlackApiError as e:
            print(f"Error fetching thread: {e}")

        return messages

    def get_current_week_messages(self) -> list[SlackMessage]:
        """
        Get all messages from the current week (Monday to Friday).
        If today is Friday, includes today's messages.
        """
        today = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Calculate the start of the week (Monday)
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)

        return self.get_channel_messages(monday, today)

    def get_week_messages(self, year: int, week_number: int) -> list[SlackMessage]:
        """
        Get all messages from a specific week.
        
        Args:
            year: The year
            week_number: ISO week number (1-52)
            
        Returns:
            List of messages from that week
        """
        # Get the Monday of the ISO week using ISO calendar
        # ISO week 1 is the week containing January 4th
        from datetime import date
        
        # Find January 4th of the year (always in week 1)
        jan4 = date(year, 1, 4)
        # Find the Monday of week 1
        week1_monday = jan4 - timedelta(days=jan4.weekday())
        # Calculate the Monday of the requested week
        first_day = datetime.combine(
            week1_monday + timedelta(weeks=week_number - 1),
            datetime.min.time()
        )
        last_day = first_day + timedelta(days=4)  # Friday
        last_day = last_day.replace(hour=23, minute=59, second=59, microsecond=999999)

        return self.get_channel_messages(first_day, last_day)

    def _parse_date_from_text(self, text: str) -> Optional[datetime]:
        """
        Extract a date from message text like "Daily report - Jan 19, 2026".
        
        Supports formats:
        - "Jan 19, 2026"
        - "January 19, 2026"
        - "Jan 19th, 2026"
        - "19 Jan 2026"
        - "2026-01-19"
        """
        import re
        from dateutil import parser as date_parser
        
        # Common date patterns in daily report headers
        date_patterns = [
            # "Jan 19, 2026" or "January 19, 2026"
            r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}',
            # "19 Jan 2026"
            r'\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}',
            # "2026-01-19"
            r'\d{4}-\d{2}-\d{2}',
            # "01/19/2026"
            r'\d{1,2}/\d{1,2}/\d{4}',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(0)
                # Remove ordinal suffixes (st, nd, rd, th)
                date_str = re.sub(r'(\d+)(?:st|nd|rd|th)', r'\1', date_str)
                try:
                    return date_parser.parse(date_str)
                except (ValueError, TypeError):
                    continue
        
        return None

    def find_daily_report_threads(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict]:
        """
        Find "Daily report" messages and fetch their thread replies.
        
        Daily reports follow the pattern: "Daily report - Month Day, Year"
        Status updates are posted as thread replies to these messages.
        
        Args:
            start_date: Start of the date range
            end_date: End of the date range
            
        Returns:
            List of dicts with 'header' (main message) and 'replies' (thread messages)
        """
        import re
        
        # Pattern to match "Daily report" messages
        daily_report_pattern = re.compile(
            r"daily\s*report|status\s*update|standup|stand-up",
            re.IGNORECASE
        )
        
        # Get all messages in the date range
        messages = self.get_channel_messages(start_date, end_date)
        
        daily_reports = []
        
        for msg in messages:
            # Check if this is a daily report header message
            if daily_report_pattern.search(msg.text):
                # Get the thread timestamp (use message ts if no thread_ts)
                thread_ts = msg.thread_ts or str(msg.timestamp.timestamp())
                
                # Fetch all thread replies
                thread_messages = self.get_thread_messages(thread_ts)
                
                # Separate header from replies (first message is the header)
                replies = [m for m in thread_messages if m.timestamp != msg.timestamp]
                
                # Try to parse the report date from the message content
                # e.g., "Daily report - Jan 19, 2026"
                report_date = self._parse_date_from_text(msg.text)
                if report_date is None:
                    # Fallback to message timestamp
                    report_date = msg.timestamp
                
                daily_reports.append({
                    'header': msg,
                    'replies': replies,
                    'date': report_date,
                })
        
        return daily_reports

    def get_weekly_status_updates(self, year: int = None, week_number: int = None) -> list[SlackMessage]:
        """
        Get all status updates from daily report threads for a specific week.
        
        Args:
            year: The year (default: current year)
            week_number: ISO week number (default: current week)
            
        Returns:
            Tuple of (all status update messages, daily report threads)
        """
        from datetime import date
        
        now = datetime.now()
        if year is None:
            year = now.year
        if week_number is None:
            week_number = now.isocalendar()[1]
        
        # Calculate week date range using ISO week
        # Find January 4th of the year (always in week 1)
        jan4 = date(year, 1, 4)
        # Find the Monday of week 1
        week1_monday = jan4 - timedelta(days=jan4.weekday())
        # Calculate the Monday of the requested week
        first_day = datetime.combine(
            week1_monday + timedelta(weeks=week_number - 1),
            datetime.min.time()
        )
        last_day = first_day + timedelta(days=6)  # Include weekend posts
        last_day = last_day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Find all daily report threads
        daily_reports = self.find_daily_report_threads(first_day, last_day)
        
        # Collect all thread replies (the actual status updates)
        all_updates = []
        for report in daily_reports:
            all_updates.extend(report['replies'])
        
        # Sort by timestamp
        all_updates.sort(key=lambda m: m.timestamp)
        
        return all_updates, daily_reports
