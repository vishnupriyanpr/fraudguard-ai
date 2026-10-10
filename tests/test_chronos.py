"""
End-to-End Verification Test Suite for CHRONOS // Sentinel
Validates Event Ingestion, Scraping, Research Synthesis, MCP Resolution,
Internal Calendar, Task Completion, and Non-Nosy Briefings.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from sentinel.main import app
from sentinel.db import init_db

client = TestClient(app)

def setup_module():
    init_db()

def test_health_and_briefing():
    resp = client.get("/api/briefing")
    assert resp.status_code == 200
    data = resp.json()
    assert "header" in data
    assert "message" in data

def test_events_listing():
    resp = client.get("/api/events")
    assert resp.status_code == 200
    events = resp.json()
    assert isinstance(events, list)

def test_create_event_pipeline():
    future_deadline = (datetime.now() + timedelta(days=3)).isoformat()
    payload = {
        "title": "Autonomous AI Agent Grant 2026",
        "deadline": future_deadline,
        "category": "grant",
        "description": "Building autonomous developer tools with persistent local agents.",
        "user_notes": "Focused on GitHub pull request automation and SQLite state tracking.",
        "links": ["https://example.com/grant-guidelines"],
        "user_focus": "Automated MCP integration"
    }
    
    resp = client.post("/api/events", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "event_id" in data
    event_id = data["event_id"]
    
    # Verify Research
    assert "research" in data
    assert len(data["research"]["clarification_questions"]) >= 3
    
    # Verify Tasks
    assert "tasks" in data
    assert len(data["tasks"]) >= 4
    
    # Verify MCPs recommended
    assert "mcps" in data
    mcp_names = [m["name"] for m in data["mcps"]]
    assert "GitHub MCP" in mcp_names or "Filesystem MCP" in mcp_names

    # Test Calendar Matrix
    cal_resp = client.get("/api/calendar")
    assert cal_resp.status_code == 200
    cal_data = cal_resp.json()
    assert any(c["id"] == f"event-{event_id}" for c in cal_data)

    # Test Task Toggling
    task_id = data["tasks"][0]["id"]
    toggle_resp = client.patch(f"/api/tasks/{task_id}/status", json={"status": "done"})
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["new_status"] == "done"

    # Test MCP Config Exporter
    export_resp = client.post(f"/api/mcps/export-config?event_id={event_id}")
    assert export_resp.status_code == 200
    assert "mcpServers" in export_resp.json()["config"]

    # Clean up test event
    del_resp = client.delete(f"/api/events/{event_id}")
    assert del_resp.status_code == 200
