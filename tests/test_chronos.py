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

def test_task_management_and_stats():
    # 1. Create task
    create_resp = client.post("/api/tasks", json={
        "event_id": 999,
        "title": "Build Agent Tools Subpage",
        "description": "Create high-fidelity task and tool management micro-frontends",
        "phase": "Phase 2: Execution",
        "priority": "critical",
        "due_date": "2026-11-20 18:00",
        "assigned_mcp": "sqlite"
    })
    assert create_resp.status_code == 200
    task_id = create_resp.json()["task_id"]

    # 2. Get task stats
    stats_resp = client.get("/api/tasks/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert "total" in stats
    assert "critical" in stats
    assert stats["total"] >= 1

    # 3. Update task
    update_resp = client.put(f"/api/tasks/{task_id}", json={
        "title": "Build Agent Tools Subpage (Updated)",
        "description": "Refined description with schema validation",
        "phase": "Phase 2: Execution",
        "priority": "high",
        "due_date": "2026-11-21 12:00",
        "assigned_mcp": "sqlite"
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "updated"

    # 4. Clean up
    del_resp = client.delete(f"/api/tasks/{task_id}")
    assert del_resp.status_code == 200

def test_agent_tool_builder_and_diagnostics():
    # 1. Check tools catalog
    cat_resp = client.get("/api/tools/catalog")
    assert cat_resp.status_code == 200
    tools = cat_resp.json()
    assert len(tools) >= 5
    tool_ids = [t["id"] for t in tools]
    assert "sqlite" in tool_ids
    assert "filesystem" in tool_ids

    # 2. Test sqlite tool execution
    test_resp = client.post("/api/tools/sqlite/test", json={
        "parameters": {"query": "SELECT count(*) FROM tasks"}
    })
    assert test_resp.status_code == 200
    res = test_resp.json()
    assert res["success"] is True
    assert res["status"] == "HEALTHY"
    assert "latency_ms" in res

    # 3. Test filesystem tool execution
    fs_resp = client.post("/api/tools/filesystem/test", json={
        "parameters": {"directory": "sentinel"}
    })
    assert fs_resp.status_code == 200
    assert fs_resp.json()["success"] is True

def test_integrations_endpoints():
    # 1. Check integrations status
    status_resp = client.get("/api/integrations/status")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert "google_calendar" in data
    assert "whatsapp" in data

    # 2. Test WhatsApp briefing dispatch
    wa_resp = client.post("/api/integrations/whatsapp/send", json={
        "recipient": "+15550199"
    })
    # If no events exist, status_code is 400 with detail or 200 if events exist
    assert wa_resp.status_code in [200, 400]
