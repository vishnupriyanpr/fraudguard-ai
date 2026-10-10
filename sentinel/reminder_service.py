"""
CHRONOS // Background Reminder & Executive Notification Daemon
Monitors deadlines, computes milestone proximity, and dispatches non-nosy,
high-signal briefings to the database and connected frontend clients.
"""

import time
import threading
from datetime import datetime
from typing import Dict, Any, List
from sentinel.db import get_events, get_tasks, create_reminder, get_reminders
from sentinel.ai_engine import generate_non_nosy_briefing
from sentinel.channel_service import broadcast_briefing_to_channels

_daemon_running = False
_last_reminded: Dict[int, float] = {}

def reminder_worker(interval_seconds: int = 30):
    """
    Continuous background loop checking deadlines and posting low-noise briefings.
    """
    global _daemon_running, _last_reminded
    while _daemon_running:
        try:
            now_ts = time.time()
            events = get_events()
            for event in events:
                if event.get("status") != "active":
                    continue
                    
                event_id = event["id"]
                # Rate limit reminders: at most once every 10 minutes per event
                # unless deadline is under 2 hours, then at most once every 3 minutes
                last_time = _last_reminded.get(event_id, 0)
                
                tasks = get_tasks(event_id)
                pending_tasks = [t for t in tasks if t.get("status") != "done"]
                
                briefing = generate_non_nosy_briefing(event, pending_tasks)
                hours_left = float(briefing.get("hours_left", "24.0"))
                
                min_interval = 180 if hours_left <= 2.0 else 600
                
                if (now_ts - last_time) >= min_interval:
                    _last_reminded[event_id] = now_ts
                    # Generate concise alert message
                    alert_text = f"[{briefing['header']}] {briefing['message']}"
                    create_reminder(
                        event_id=event_id,
                        message=alert_text,
                        severity=briefing["severity"]
                    )
                    # Broadcast to WhatsApp, Telegram, Discord, etc.
                    broadcast_briefing_to_channels(alert_text)
        except Exception as e:
            print(f"[CHRONOS Daemon Error]: {e}")
            
        time.sleep(interval_seconds)

def start_reminder_daemon():
    global _daemon_running
    if not _daemon_running:
        _daemon_running = True
        t = threading.Thread(target=reminder_worker, daemon=True, name="ChronosReminderDaemon")
        t.start()
        print("[CHRONOS] Executive reminder daemon started.")

def stop_reminder_daemon():
    global _daemon_running
    _daemon_running = False
