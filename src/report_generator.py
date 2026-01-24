"""
Report generator that creates weekly summary reports from aggregated status data.
"""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from .message_parser import DailyStatus, StatusAggregator, Task


@dataclass
class ReportSection:
    """Represents a section of the report."""
    title: str
    items: list[str]


class ReportGenerator:
    """
    Generates weekly summary reports in the specified format.
    
    Report Format:
    1. NOTES
    2. DONE
    3. IN PROGRESS
    4. NEXT PLAN
    5. QUESTIONS/BLOCKERS
    """

    def __init__(
        self, 
        sender_name: str = "Report Generator",
        sender_email: str = "",
        recipients_to: list[str] = None,
        recipients_cc: list[str] = None,
    ):
        """Initialize the report generator."""
        self.sender_name = sender_name
        self.sender_email = sender_email
        self.recipients_to = recipients_to or []
        self.recipients_cc = recipients_cc or []
        self.aggregator = StatusAggregator()

    def generate(
        self,
        statuses: list[DailyStatus],
        notes: list[str] = None,
    ) -> str:
        """
        Generate a weekly report from daily status updates.
        
        Args:
            statuses: List of daily status updates from the week
            notes: Additional notes to include in the report
            
        Returns:
            Formatted report string
        """
        if not statuses:
            return self._generate_empty_report()

        # Aggregate all statuses
        aggregated = self.aggregator.aggregate(statuses)
        
        # Generate report sections
        report_parts = []
        
        # Header
        report_parts.append(self._generate_header(aggregated))
        
        # 1. NOTES
        report_parts.append(self._generate_notes_section(aggregated, notes))
        
        # 2. DONE
        report_parts.append(self._generate_done_section(aggregated))
        
        # 3. IN PROGRESS
        report_parts.append(self._generate_in_progress_section(aggregated))
        
        # 4. NEXT PLAN
        report_parts.append(self._generate_next_plan_section(aggregated))
        
        # 5. QUESTIONS/BLOCKERS
        report_parts.append(self._generate_blockers_section(aggregated))
        
        # Footer
        report_parts.append(self._generate_footer())
        
        return "\n".join(filter(None, report_parts))

    def _generate_header(self, aggregated: dict) -> str:
        """Generate the report header."""
        now = datetime.now()
        
        # Format date range
        start_date = aggregated["date_range"]["start"]
        end_date = aggregated["date_range"]["end"]
        
        if start_date and end_date:
            date_range = f"{start_date.strftime('%B %d')} to {end_date.strftime('%B %d, %Y')}"
        else:
            # Default to current week
            date_range = f"the current week ending {now.strftime('%B %d, %Y')}"
        
        # Build sender line
        if self.sender_email:
            sender_line = f"{self.sender_name} <{self.sender_email}>"
        else:
            sender_line = self.sender_name
        
        lines = [
            sender_line,
            now.strftime("%b %d, %Y, %I:%M %p"),
        ]
        
        # Add recipients
        if self.recipients_to:
            lines.append(f"to: {', '.join(self.recipients_to)}")
        
        if self.recipients_cc:
            lines.append(f"cc: {', '.join(self.recipients_cc)}")
        
        lines.extend([
            "",
            "Hi all,",
            "",
            "Hope you are doing well!",
            "",
            f"Please find below the End of Week Update covering the period from {date_range}:",
            "",
        ])
        
        return "\n".join(lines)

    def _generate_notes_section(
        self, 
        aggregated: dict, 
        additional_notes: list[str] = None
    ) -> str:
        """Generate the NOTES section."""
        lines = ["1. NOTES"]
        
        notes = aggregated.get("notes", [])
        if additional_notes:
            notes.extend(additional_notes)
        
        if notes:
            for note in notes:
                lines.append(f"- {note}")
        else:
            lines.append("- No special notes this week")
        
        lines.append("")
        return "\n".join(lines)

    def _generate_done_section(self, aggregated: dict) -> str:
        """Generate the DONE section grouped by category/assignee."""
        lines = ["2. DONE"]
        
        done_tasks = aggregated.get("done", {})
        
        if not done_tasks:
            lines.append("- No completed tasks this week")
            lines.append("")
            return "\n".join(lines)
        
        # Group tasks by category (inferred from ticket patterns or descriptions)
        categorized = self._categorize_tasks(done_tasks)
        
        for category, tasks_by_assignee in categorized.items():
            if tasks_by_assignee:
                lines.append(f"\n{category}")
                lines.append("")
                
                for assignee, tasks in tasks_by_assignee.items():
                    for task in tasks:
                        task_line = self._format_task(task)
                        lines.append(task_line)
        
        lines.append("")
        return "\n".join(lines)

    def _generate_in_progress_section(self, aggregated: dict) -> str:
        """Generate the IN PROGRESS section."""
        lines = ["3. IN PROGRESS"]
        
        in_progress = aggregated.get("in_progress", {})
        
        if not in_progress:
            lines.append("- No tasks currently in progress")
            lines.append("")
            return "\n".join(lines)
        
        for assignee, tasks in in_progress.items():
            for task in tasks:
                task_line = self._format_task(task)
                lines.append(task_line)
        
        lines.append("")
        return "\n".join(lines)

    def _generate_next_plan_section(self, aggregated: dict) -> str:
        """Generate the NEXT PLAN section."""
        lines = ["4. NEXT PLAN"]
        
        planned = aggregated.get("planned", {})
        
        if not planned:
            lines.append("- Planning to continue with assigned tasks")
            lines.append("")
            return "\n".join(lines)
        
        for assignee, tasks in planned.items():
            for task in tasks:
                task_line = self._format_task(task)
                lines.append(task_line)
        
        lines.append("")
        return "\n".join(lines)

    def _generate_blockers_section(self, aggregated: dict) -> str:
        """Generate the QUESTIONS/BLOCKERS section."""
        lines = ["5. QUESTIONS/BLOCKERS"]
        
        blockers = aggregated.get("blockers", [])
        
        if not blockers:
            lines.append("- No blockers this week")
        else:
            for blocker in blockers:
                lines.append(f"- {blocker}")
        
        lines.append("")
        return "\n".join(lines)

    def _generate_footer(self) -> str:
        """Generate the report footer."""
        return "\n".join([
            "Please let us know if you have any questions or concerns.",
            "",
            "Thanks and Best regards,",
            self.sender_name,
        ])

    def _generate_empty_report(self) -> str:
        """Generate a report when no status updates are found."""
        now = datetime.now()
        return f"""No status updates found for this week.

Please ensure team members have posted their daily status updates in the Slack channel.

Generated on: {now.strftime('%B %d, %Y at %I:%M %p')}
"""

    def _format_task(self, task: Task) -> str:
        """Format a single task for display."""
        parts = []
        
        # Add ticket ID if present
        if task.ticket_id:
            parts.append(f"{task.ticket_id}:")
        
        # Add description
        parts.append(task.description)
        
        # Add PR reference if present
        if task.pr_number:
            parts.append(f"- PR #{task.pr_number}")
        
        # Add assignee
        parts.append(f"- @{task.assignee}")
        
        return " ".join(parts)

    def _categorize_tasks(self, tasks_by_assignee: dict) -> dict:
        """
        Categorize tasks into logical groups.
        
        Categories:
        - Feature Development
        - Bug Fixes
        - Code & Infrastructure
        - Documentation
        - Onboarding
        - Other
        """
        categories = {
            "Feature Development": {},
            "Bug Fixes": {},
            "Code & Infrastructure": {},
            "Documentation": {},
            "New Team Member Onboarding": {},
            "Other": {},
        }
        
        # Keywords for categorization
        category_keywords = {
            "Feature Development": [
                "feature", "implement", "add", "create", "build", "develop",
                "show", "display", "handle", "print", "export", "v2-", "v1-"
            ],
            "Bug Fixes": [
                "fix", "bug", "issue", "error", "patch", "resolve", "correct"
            ],
            "Code & Infrastructure": [
                "refactor", "clean", "remove", "update", "deploy", "infrastructure",
                "database", "api", "config", "setup", "pr", "code review",
                "swagger", "postman", "dump", "migration"
            ],
            "Documentation": [
                "doc", "readme", "comment", "guide", "tutorial", "overview"
            ],
            "New Team Member Onboarding": [
                "onboard", "setup", "environment", "local", "new team", "welcome",
                "training", "overview session", "familiarization"
            ],
        }
        
        for assignee, tasks in tasks_by_assignee.items():
            for task in tasks:
                description_lower = task.description.lower()
                ticket_lower = (task.ticket_id or "").lower()
                
                categorized = False
                for category, keywords in category_keywords.items():
                    for keyword in keywords:
                        if keyword in description_lower or keyword in ticket_lower:
                            if assignee not in categories[category]:
                                categories[category][assignee] = []
                            categories[category][assignee].append(task)
                            categorized = True
                            break
                    if categorized:
                        break
                
                if not categorized:
                    if assignee not in categories["Other"]:
                        categories["Other"][assignee] = []
                    categories["Other"][assignee].append(task)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}


class GroqReportEnhancer:
    """
    Uses Groq AI to enhance and summarize reports.
    Optional feature that improves report quality with AI assistance.
    """

    GROQ_BASE_URL = "https://api.groq.com/openai/v1"
    GROQ_MODEL = "llama-3.3-70b-versatile"

    REPORT_TEMPLATE = """Hi all,

Hope you are doing well!

Please find below the End of Week Update covering the period from {date_range}:

1. NOTES
{notes}

2. DONE
{done_section}

3. IN PROGRESS
{in_progress_section}

4. NEXT PLAN
{next_plan_section}

5. QUESTIONS/BLOCKERS
{blockers_section}

Please let us know if you have any questions or concerns.

Thanks and Best regards,"""

    def __init__(self, api_key: str):
        """Initialize with Groq API key."""
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=api_key,
                base_url=self.GROQ_BASE_URL,
            )
            self.available = True
        except ImportError:
            self.available = False
            print("OpenAI package not installed. Groq AI enhancement disabled.")

    def enhance_report(self, raw_messages: list[str], date_range: str, sender_name: str = "") -> str:
        """
        Use Groq AI to generate an enhanced report from raw messages.
        
        Args:
            raw_messages: List of raw status update messages
            date_range: Date range string (e.g., "January 19th to January 23rd, 2026")
            sender_name: Name of the report sender
            
        Returns:
            AI-enhanced report
        """
        if not self.available:
            return None

        prompt = f"""You are creating a weekly status report for a software development team. Parse the daily status updates and create a consolidated report.

## OUTPUT FORMAT (follow exactly):

Hi all,

Hope you are doing well!

Please find below the End of Week Update covering the period from {date_range}:

1. NOTES
[2-4 high-level bullet points summarizing key achievements, milestones, or important events from the week]

2. DONE
Feature Development

[List completed features with format: V2-XXX: Description - PR #YYY ready for review - @AssigneeName]

Code & Infrastructure

[List infrastructure/code improvements with format: Description - @AssigneeName]

Bug Fixes

[List bug fixes if any, with format: V2-XXX: Description - @AssigneeName]

3. IN PROGRESS
[List items currently being worked on with format: V2-XXX: Description - @AssigneeName]

4. NEXT PLAN
[List planned items with format: Description - @AssigneeName]

5. QUESTIONS/BLOCKERS
[List any questions or blockers with format: V2-XXX: Question/blocker description - @AssigneeName]
[If no blockers: "No blockers this week"]

Please let us know if you have any questions or concerns.

Thanks and Best regards,
{sender_name}

## RULES:
1. Extract ticket IDs (V2-XXX format) and include them
2. Extract PR numbers and format as "PR #XXX"
3. Include @AssigneeName for each item (extract from the status updates)
4. Group DONE items by category: Feature Development, Code & Infrastructure, Bug Fixes
5. Deduplicate - if same ticket appears multiple days, only list once in most appropriate section
6. Items marked "Ready for review" or "Ready for release" go in DONE
7. Items marked "In Progress" go in IN PROGRESS
8. Items marked "Next plan" go in NEXT PLAN
9. Items marked "Questions" or "Blockers" go in QUESTIONS/BLOCKERS
10. Keep descriptions concise but informative
11. Remove Slack formatting like <URL|text> - just keep the text
12. Do NOT include empty categories

## RAW STATUS UPDATES FROM THE WEEK:

{chr(10).join(raw_messages)}

Generate the report now:"""

        try:
            response = self.client.chat.completions.create(
                model=self.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional technical writer. Create clear, well-organized status reports. Follow the output format exactly."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=4000,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Groq AI enhancement failed: {e}")
            return None

    def summarize_notes(self, tasks: list[str]) -> list[str]:
        """Generate summary notes from a list of tasks."""
        if not self.available or not tasks:
            return []

        prompt = f"""Based on these completed tasks from a software development team this week, generate 2-4 brief, high-level summary notes that capture the main themes/achievements:

Tasks:
{chr(10).join(f'- {task}' for task in tasks)}

Return only the summary notes as a bullet list, no other text."""

        try:
            response = self.client.chat.completions.create(
                model=self.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=500,
            )
            
            notes = []
            for line in response.choices[0].message.content.split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("•"):
                    notes.append(line[1:].strip())
                elif line:
                    notes.append(line)
            
            return notes[:4]  # Maximum 4 notes
        except Exception as e:
            print(f"Groq note summarization failed: {e}")
            return []


# Alias for backward compatibility
AIReportEnhancer = GroqReportEnhancer
