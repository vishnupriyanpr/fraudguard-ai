"""
CHRONOS // SQLite Persistence Layer
Manages local storage for Events, Links, Research Dossiers, Tasks, MCP Configs, and Reminders.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chronos.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Events Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT DEFAULT 'hackathon',
        deadline TEXT NOT NULL,
        description TEXT,
        user_notes TEXT,
        status TEXT DEFAULT 'active',
        created_at TEXT NOT NULL
    )
    """)
    
    # 2. Event Links Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS event_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        url TEXT NOT NULL,
        title TEXT,
        scraped_content TEXT,
        summary TEXT,
        status TEXT DEFAULT 'pending',
        scraped_at TEXT,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
    )
    """)
    
    # 3. Event Research Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS event_research (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER UNIQUE NOT NULL,
        summary TEXT,
        key_deadlines TEXT,
        requirements TEXT,
        tracks_or_prizes TEXT,
        recommended_stack TEXT,
        clarification_questions TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
    )
    """)
    
    # 4. Tasks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        phase TEXT DEFAULT 'Phase 1: Setup',
        due_date TEXT,
        status TEXT DEFAULT 'pending',
        priority TEXT DEFAULT 'high',
        assigned_mcp TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
    )
    """)
    
    # 5. MCP Configs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mcp_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        mcp_name TEXT NOT NULL,
        description TEXT,
        install_command TEXT,
        config_json TEXT,
        is_installed INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
    )
    """)
    
    # 6. Reminders / Briefings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        task_id INTEGER,
        message TEXT NOT NULL,
        severity TEXT DEFAULT 'info',
        is_read INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
    )
    """)

    # 7. Conversational Chat History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        card_type TEXT,
        metadata TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # 8. Multi-Platform Notification Channels Table (WhatsApp, Telegram, Discord, Slack)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notification_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT NOT NULL,
        target TEXT NOT NULL,
        webhook_url TEXT,
        api_token TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()

# Event Operations
def create_event(title: str, deadline: str, category: str = 'hackathon', description: str = '', user_notes: str = '') -> int:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO events (title, category, deadline, description, user_notes, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'active', ?)
    """, (title, category, deadline, description, user_notes, now))
    event_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return event_id

def get_events() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events ORDER BY deadline ASC")
    rows = cursor.fetchall()
    events = [dict(row) for row in rows]
    conn.close()
    return events

def get_event(event_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_event(event_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
    cursor.execute("DELETE FROM event_links WHERE event_id = ?", (event_id,))
    cursor.execute("DELETE FROM event_research WHERE event_id = ?", (event_id,))
    cursor.execute("DELETE FROM tasks WHERE event_id = ?", (event_id,))
    cursor.execute("DELETE FROM mcp_configs WHERE event_id = ?", (event_id,))
    cursor.execute("DELETE FROM reminders WHERE event_id = ?", (event_id,))
    conn.commit()
    conn.close()

# Links Operations
def add_event_link(event_id: int, url: str, title: str = '') -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO event_links (event_id, url, title, status)
        VALUES (?, ?, ?, 'pending')
    """, (event_id, url, title or url))
    link_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return link_id

def update_event_link(link_id: int, title: str, scraped_content: str, summary: str, status: str = 'scraped'):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        UPDATE event_links
        SET title = ?, scraped_content = ?, summary = ?, status = ?, scraped_at = ?
        WHERE id = ?
    """, (title, scraped_content, summary, status, now, link_id))
    conn.commit()
    conn.close()

def get_event_links(event_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM event_links WHERE event_id = ?", (event_id,))
    rows = cursor.fetchall()
    links = [dict(row) for row in rows]
    conn.close()
    return links

# Research Operations
def save_event_research(event_id: int, summary: str, key_deadlines: list, requirements: list, 
                        tracks_or_prizes: list, recommended_stack: list, clarification_questions: list):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT OR REPLACE INTO event_research 
        (event_id, summary, key_deadlines, requirements, tracks_or_prizes, recommended_stack, clarification_questions, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id,
        summary,
        json.dumps(key_deadlines),
        json.dumps(requirements),
        json.dumps(tracks_or_prizes),
        json.dumps(recommended_stack),
        json.dumps(clarification_questions),
        now
    ))
    conn.commit()
    conn.close()

def get_event_research(event_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM event_research WHERE event_id = ?", (event_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    data = dict(row)
    data["key_deadlines"] = json.loads(data["key_deadlines"] or "[]")
    data["requirements"] = json.loads(data["requirements"] or "[]")
    data["tracks_or_prizes"] = json.loads(data["tracks_or_prizes"] or "[]")
    data["recommended_stack"] = json.loads(data["recommended_stack"] or "[]")
    data["clarification_questions"] = json.loads(data["clarification_questions"] or "[]")
    return data

# Tasks Operations
def create_task(event_id: int, title: str, description: str = '', phase: str = 'Phase 1: Setup', 
                due_date: str = '', priority: str = 'high', assigned_mcp: str = '') -> int:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO tasks (event_id, title, description, phase, due_date, status, priority, assigned_mcp, created_at)
        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?)
    """, (event_id, title, description, phase, due_date, priority, assigned_mcp, now))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id

def get_tasks(event_id: Optional[int] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if event_id:
        cursor.execute("SELECT * FROM tasks WHERE event_id = ? ORDER BY due_date ASC", (event_id,))
    else:
        cursor.execute("SELECT * FROM tasks ORDER BY due_date ASC")
    rows = cursor.fetchall()
    tasks = [dict(row) for row in rows]
    conn.close()
    return tasks

def update_task_status(task_id: int, status: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

# MCP Configs Operations
def save_mcp_config(event_id: int, mcp_name: str, description: str, install_command: str, config_json: dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO mcp_configs (event_id, mcp_name, description, install_command, config_json, is_installed, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, 0, 1, ?)
    """, (event_id, mcp_name, description, install_command, json.dumps(config_json), now))
    mcp_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return mcp_id

def get_mcp_configs(event_id: Optional[int] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if event_id:
        cursor.execute("SELECT * FROM mcp_configs WHERE event_id = ?", (event_id,))
    else:
        cursor.execute("SELECT * FROM mcp_configs")
    rows = cursor.fetchall()
    configs = []
    for row in rows:
        d = dict(row)
        try:
            d["config_json"] = json.loads(d["config_json"])
        except Exception:
            pass
        configs.append(d)
    conn.close()
    return configs

def update_mcp_status(mcp_id: int, is_installed: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE mcp_configs SET is_installed = ? WHERE id = ?", (is_installed, mcp_id))
    conn.commit()
    conn.close()

# Reminder Operations
def create_reminder(event_id: Optional[int], message: str, severity: str = 'info', task_id: Optional[int] = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO reminders (event_id, task_id, message, severity, is_read, created_at)
        VALUES (?, ?, ?, ?, 0, ?)
    """, (event_id, task_id, message, severity, now))
    reminder_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return reminder_id

def get_reminders(limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reminders ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    reminders = [dict(row) for row in rows]
    conn.close()
    return reminders

def mark_reminders_read():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE reminders SET is_read = 1")
    conn.commit()
    conn.close()

# Chat Operations
def save_chat_message(role: str, content: str, card_type: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO chat_messages (role, content, card_type, metadata, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (role, content, card_type, json.dumps(metadata or {}), now))
    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return msg_id

def get_chat_history(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chat_messages ORDER BY id ASC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    messages = []
    for r in rows:
        d = dict(r)
        try:
            d["metadata"] = json.loads(d["metadata"] or "{}")
        except Exception:
            d["metadata"] = {}
        messages.append(d)
    conn.close()
    return messages

def clear_chat_history():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_messages")
    conn.commit()
    conn.close()

# Notification Channel Operations (WhatsApp, Telegram, Discord, Slack)
def save_notification_channel(platform: str, target: str, webhook_url: Optional[str] = None, api_token: Optional[str] = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO notification_channels (platform, target, webhook_url, api_token, is_active, created_at)
        VALUES (?, ?, ?, ?, 1, ?)
    """, (platform, target, webhook_url or "", api_token or "", now))
    channel_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return channel_id

def get_notification_channels() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notification_channels WHERE is_active = 1 ORDER BY id DESC")
    rows = cursor.fetchall()
    channels = [dict(r) for r in rows]
    conn.close()
    return channels

def delete_notification_channel(channel_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notification_channels WHERE id = ?", (channel_id,))
    conn.commit()
    conn.close()
