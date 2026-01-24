#!/usr/bin/env python3
"""
Main entry point for the Slack Report Generator.

This script reads daily status updates from a Slack channel and generates
weekly summary reports.

Usage:
    python main.py generate              # Generate report for current week
    python main.py generate --week 3     # Generate for specific week
    python main.py generate --ai         # Use AI enhancement
    python main.py preview               # Preview daily reports
    python main.py send <file>           # Send report via email
"""

from src.cli import main

if __name__ == "__main__":
    main()
