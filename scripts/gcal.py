#!/usr/bin/env python3
"""
scripts/gcal.py - Autonomous Google Calendar CLI Integration
Adheres to the google-calendar-automation skill:
- Lists upcoming milestones
- Exports RFC 5545 iCalendar (.ics) files with tiered alarms
- Generates 1-click Google Calendar web event URLs
"""

import sys
import os
import argparse
from datetime import datetime, timezone

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sentinel.db import get_events, get_tasks
from sentinel.integrations import gcal_connector

def list_events():
    events = get_events()
    if not events:
        print("[GCAL] No events found in CHRONOS database.")
        return
    print(f"\n[CHRONOS CALENDAR] Found {len(events)} registered events:")
    for ev in events:
        print(f" • [{ev.get('category', 'project').upper()}] {ev.get('title')} (Due: {ev.get('deadline')})")

def export_ics(output_path="chronos_calendar.ics"):
    events = get_events()
    tasks = []
    for ev in events:
        tasks.extend(get_tasks(ev["id"]))
    
    ics_content = gcal_connector.generate_icalendar("CHRONOS // Workspaces & Deadlines", None, tasks)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ics_content)
    print(f"[GCAL] Exported {len(tasks)} milestones to {output_path} with -24h, -2h, -30m tiered alarms.")

def create_event(title: str, start: str, end: str, description: str = ""):
    res = gcal_connector.build_google_calendar_url(
        title=f"[CHRONOS] {title}",
        start_dt=datetime.fromisoformat(start).replace(tzinfo=timezone.utc),
        end_dt=datetime.fromisoformat(end).replace(tzinfo=timezone.utc),
        description=description or "CHRONOS Autonomous Milestone Gate"
    )
    print(f"[GCAL] 1-Click Web Event URL:\n{res}")

def main():
    parser = argparse.ArgumentParser(description="CHRONOS Google Calendar CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list-events", help="List calendar milestones")
    
    export_parser = subparsers.add_parser("export-ics", help="Export RFC 5545 iCalendar .ics file")
    export_parser.add_argument("--output", default="chronos_calendar.ics", help="Output .ics file path")

    create_parser = subparsers.add_parser("create-event", help="Generate 1-click web calendar event")
    create_parser.add_argument("title", help="Event title")
    create_parser.add_argument("start", help="Start datetime (ISO)")
    create_parser.add_argument("end", help="End datetime (ISO)")
    create_parser.add_argument("--description", default="", help="Description")

    args = parser.parse_args()

    if args.command == "list-events":
        list_events()
    elif args.command == "export-ics":
        export_ics(args.output)
    elif args.command == "create-event":
        create_event(args.title, args.start, args.end, args.description)
    else:
        list_events()

if __name__ == "__main__":
    main()
