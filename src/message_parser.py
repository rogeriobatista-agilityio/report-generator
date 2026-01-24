"""
Parser for extracting status updates from Slack messages.
"""

import re
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from .slack_client import SlackMessage


class TaskStatus(Enum):
    """Status of a task."""
    DONE = "done"
    IN_PROGRESS = "in_progress"
    PLANNED = "planned"
    BLOCKED = "blocked"


@dataclass
class Task:
    """Represents a single task from a status update."""
    description: str
    assignee: str
    status: TaskStatus
    ticket_id: Optional[str] = None
    pr_number: Optional[str] = None


@dataclass
class DailyStatus:
    """Represents a daily status update from a team member."""
    author: str
    date: datetime
    done: list[Task] = field(default_factory=list)
    in_progress: list[Task] = field(default_factory=list)
    planned: list[Task] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    raw_text: str = ""


class MessageParser:
    """Parser for extracting status updates from Slack messages."""

    # Common patterns for status updates
    SECTION_PATTERNS = {
        "done": [
            r"(?:done|completed|finished|accomplished)[\s:]*",
            r"(?:what i did|what i've done|yesterday|today i did)[\s:]*",
            r"✅[\s:]*",
        ],
        "in_progress": [
            r"(?:in progress|working on|currently|ongoing)[\s:]*",
            r"(?:today|doing today|working today)[\s:]*",
            r"🔄[\s:]*",
        ],
        "planned": [
            r"(?:planned|next|tomorrow|will do|planning to)[\s:]*",
            r"(?:next steps|upcoming|goals)[\s:]*",
            r"📋[\s:]*",
        ],
        "blockers": [
            r"(?:blocked|blockers|issues|problems|stuck)[\s:]*",
            r"(?:need help|questions|concerns)[\s:]*",
            r"🚫[\s:]*",
            r"❓[\s:]*",
        ],
    }

    # Pattern to extract ticket IDs (e.g., V2-749, JIRA-123)
    TICKET_PATTERN = r"([A-Z]+-\d+)"
    
    # Pattern to extract PR numbers (e.g., PR #670, #670)
    PR_PATTERN = r"(?:PR\s*)?#(\d+)"

    # Pattern to extract assignee (e.g., @Binh Huynh, @rogerio)
    ASSIGNEE_PATTERN = r"@([A-Za-z]+(?:\s+[A-Za-z]+)?)"

    def __init__(self):
        """Initialize the parser."""
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        self.compiled_sections = {}
        for section, patterns in self.SECTION_PATTERNS.items():
            self.compiled_sections[section] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
        
        self.ticket_re = re.compile(self.TICKET_PATTERN)
        self.pr_re = re.compile(self.PR_PATTERN)
        self.assignee_re = re.compile(self.ASSIGNEE_PATTERN)

    def is_status_update(self, message: SlackMessage) -> bool:
        """
        Determine if a message is likely a status update.
        
        Heuristics:
        - Contains section headers (done, in progress, etc.)
        - Contains bullet points or numbered lists
        - Contains ticket IDs
        - Has reasonable length (not too short)
        """
        text = message.text.lower()
        
        # Check for section headers
        section_keywords = ["done", "completed", "in progress", "working on", 
                          "blocked", "next", "planned", "today", "yesterday"]
        has_sections = sum(1 for kw in section_keywords if kw in text) >= 2
        
        # Check for list indicators
        has_lists = bool(re.search(r"(?:^|\n)\s*[-•*\d.]\s+", message.text))
        
        # Check for ticket IDs
        has_tickets = bool(self.ticket_re.search(message.text))
        
        # Check minimum length
        has_length = len(message.text) > 100

        # Score the message
        score = sum([has_sections, has_lists, has_tickets, has_length])
        return score >= 2

    def parse_message(self, message: SlackMessage) -> Optional[DailyStatus]:
        """
        Parse a Slack message into a DailyStatus object.
        
        Args:
            message: The Slack message to parse
            
        Returns:
            DailyStatus object if the message is a status update, None otherwise
        """
        if not self.is_status_update(message):
            return None

        status = DailyStatus(
            author=message.user_name,
            date=message.timestamp,
            raw_text=message.text,
        )

        # Parse sections
        sections = self._split_into_sections(message.text)
        
        for section_type, content in sections.items():
            tasks = self._parse_tasks(content, message.user_name)
            
            if section_type == "done":
                status.done = tasks
            elif section_type == "in_progress":
                status.in_progress = tasks
            elif section_type == "planned":
                status.planned = tasks
            elif section_type == "blockers":
                status.blockers = [t.description for t in tasks]

        return status

    def _split_into_sections(self, text: str) -> dict[str, str]:
        """Split message text into sections based on headers."""
        sections = {}
        lines = text.split("\n")
        
        current_section = None
        current_content = []

        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if this line is a section header
            detected_section = None
            for section_type, patterns in self.compiled_sections.items():
                for pattern in patterns:
                    if pattern.match(line_lower):
                        detected_section = section_type
                        break
                if detected_section:
                    break

            if detected_section:
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content)
                
                current_section = detected_section
                current_content = []
            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content)

        return sections

    def _parse_tasks(self, content: str, default_assignee: str) -> list[Task]:
        """Parse tasks from section content."""
        tasks = []
        
        # Split by bullet points or numbered lists
        items = re.split(r"(?:^|\n)\s*[-•*]\s*|\n\s*\d+\.\s*", content)
        
        for item in items:
            item = item.strip()
            if not item or len(item) < 5:
                continue

            # Extract ticket ID
            ticket_match = self.ticket_re.search(item)
            ticket_id = ticket_match.group(1) if ticket_match else None

            # Extract PR number
            pr_match = self.pr_re.search(item)
            pr_number = pr_match.group(1) if pr_match else None

            # Extract assignee
            assignee_match = self.assignee_re.search(item)
            assignee = assignee_match.group(1) if assignee_match else default_assignee

            # Clean description
            description = item
            # Remove assignee mention from description
            description = self.assignee_re.sub("", description).strip()
            # Clean up trailing dashes or hyphens
            description = re.sub(r"\s*[-–—]\s*$", "", description).strip()

            if description:
                tasks.append(Task(
                    description=description,
                    assignee=assignee,
                    status=TaskStatus.DONE,  # Will be set by caller
                    ticket_id=ticket_id,
                    pr_number=pr_number,
                ))

        return tasks

    def parse_messages(self, messages: list[SlackMessage]) -> list[DailyStatus]:
        """
        Parse multiple messages and return status updates.
        
        Args:
            messages: List of Slack messages
            
        Returns:
            List of parsed DailyStatus objects
        """
        statuses = []
        for msg in messages:
            status = self.parse_message(msg)
            if status:
                statuses.append(status)
        return statuses


class StatusAggregator:
    """Aggregates multiple daily statuses into a weekly summary."""

    def __init__(self):
        """Initialize the aggregator."""
        self.parser = MessageParser()

    def aggregate(self, statuses: list[DailyStatus]) -> dict:
        """
        Aggregate multiple daily statuses into a weekly summary.
        
        Args:
            statuses: List of daily status updates
            
        Returns:
            Dictionary with aggregated data by category and assignee
        """
        aggregated = {
            "done": {},  # assignee -> list of tasks
            "in_progress": {},
            "planned": {},
            "blockers": [],
            "notes": [],
            "authors": set(),
            "date_range": {
                "start": None,
                "end": None,
            }
        }

        for status in statuses:
            aggregated["authors"].add(status.author)
            
            # Track date range
            if aggregated["date_range"]["start"] is None:
                aggregated["date_range"]["start"] = status.date
            else:
                aggregated["date_range"]["start"] = min(
                    aggregated["date_range"]["start"], status.date
                )
            
            if aggregated["date_range"]["end"] is None:
                aggregated["date_range"]["end"] = status.date
            else:
                aggregated["date_range"]["end"] = max(
                    aggregated["date_range"]["end"], status.date
                )

            # Aggregate tasks by assignee
            for task in status.done:
                if task.assignee not in aggregated["done"]:
                    aggregated["done"][task.assignee] = []
                aggregated["done"][task.assignee].append(task)

            for task in status.in_progress:
                if task.assignee not in aggregated["in_progress"]:
                    aggregated["in_progress"][task.assignee] = []
                aggregated["in_progress"][task.assignee].append(task)

            for task in status.planned:
                if task.assignee not in aggregated["planned"]:
                    aggregated["planned"][task.assignee] = []
                aggregated["planned"][task.assignee].append(task)

            aggregated["blockers"].extend(status.blockers)
            aggregated["notes"].extend(status.notes)

        # Convert authors set to list
        aggregated["authors"] = list(aggregated["authors"])
        
        # Deduplicate tasks (same ticket or similar description)
        aggregated = self._deduplicate_tasks(aggregated)

        return aggregated

    def _deduplicate_tasks(self, aggregated: dict) -> dict:
        """Remove duplicate tasks based on ticket ID or similar descriptions."""
        for category in ["done", "in_progress", "planned"]:
            for assignee, tasks in aggregated[category].items():
                seen_tickets = set()
                seen_descriptions = set()
                unique_tasks = []
                
                for task in tasks:
                    # Check by ticket ID first
                    if task.ticket_id:
                        if task.ticket_id not in seen_tickets:
                            seen_tickets.add(task.ticket_id)
                            unique_tasks.append(task)
                    else:
                        # Normalize description for comparison
                        normalized = task.description.lower().strip()[:50]
                        if normalized not in seen_descriptions:
                            seen_descriptions.add(normalized)
                            unique_tasks.append(task)
                
                aggregated[category][assignee] = unique_tasks

        # Deduplicate blockers
        aggregated["blockers"] = list(set(aggregated["blockers"]))
        aggregated["notes"] = list(set(aggregated["notes"]))

        return aggregated
