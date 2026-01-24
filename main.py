#!/usr/bin/env python3
"""
Main entry point for the Automated Slack Report Generator.

This script reads daily status updates from a Slack channel and generates
weekly summary reports every Friday.

Usage:
    python main.py                    # Generate report for current week
    python main.py --week 3 --year 2026  # Generate for specific week
    python main.py --output report.txt   # Save to file
    python main.py --ai               # Use AI enhancement
"""

from src.cli import main

if __name__ == "__main__":
    main()
