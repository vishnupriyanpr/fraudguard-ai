"""
CHRONOS // FastAPI Server & Application Root
Local backend orchestrator connecting Link Scraper, Research Synthesizer,
Task Decomposer, MCP Integrator, Internal Calendar, and Executive Notifications.
"""

import os
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from sentinel.db import (
    init_db, create_event, get_events, get_event, delete_event,
    add_event_link, update_event_link, get_event_links,
    save_event_research, get_event_research,
    create_task, get_tasks, update_task_status, delete_task,
    save_mcp_config, get_mcp_configs, update_mcp_status,
    create_reminder, get_reminders, mark_reminders_read
)
from sentinel.scraper import scrape_event_url
from sentinel.ai_engine import (
    synthesize_research, generate_phased_tasks, generate_non_nosy_briefing
)
from sentinel.mcp_manager import (
    recommend_mcps_for_event, generate_unified_config, save_mcp_config_to_disk, MCP_CATALOG
)
from sentinel.reminder_service import start_reminder_daemon, stop_reminder_daemon

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_reminder_daemon()
    yield
    stop_reminder_daemon()

app = FastAPI(title="CHRONOS", description="Autonomous Event Deadline Sentinel & MCP Orchestrator", lifespan=lifespan)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Request Schemas
class EventCreateRequest(BaseModel):
    title: str
    deadline: str
    category: Optional[str] = "hackathon"
    description: Optional[str] = ""
    user_notes: Optional[str] = ""
    links: Optional[List[str]] = []
    user_focus: Optional[str] = ""

class TaskCreateRequest(BaseModel):
    event_id: int
    title: str
    description: Optional[str] = ""
    phase: Optional[str] = "Phase 1: Setup"
    due_date: Optional[str] = ""
    priority: Optional[str] = "high"
    assigned_mcp: Optional[str] = ""

class TaskStatusUpdateRequest(BaseModel):
    status: str

class LinkAddRequest(BaseModel):
    url: str
    title: Optional[str] = ""

class ResearchRefineRequest(BaseModel):
    user_focus: str

# Endpoints
@app.get("/")
def serve_home():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "CHRONOS API is active. Static UI initializing."}

@app.get("/api/events")
def list_events():
    events = get_events()
    enhanced = []
    for ev in events:
        ev_id = ev["id"]
        tasks = get_tasks(ev_id)
        done_count = sum(1 for t in tasks if t["status"] == "done")
        total_tasks = len(tasks)
        ev_dict = dict(ev)
        ev_dict["task_count"] = total_tasks
        ev_dict["done_count"] = done_count
        ev_dict["progress"] = int((done_count / total_tasks * 100)) if total_tasks > 0 else 0
        enhanced.append(ev_dict)
    return enhanced

@app.post("/api/events")
def create_event_pipeline(req: EventCreateRequest):
    # 1. Create base event
    event_id = create_event(
        title=req.title,
        deadline=req.deadline,
        category=req.category or "hackathon",
        description=req.description or "",
        user_notes=req.user_notes or ""
    )
    
    # 2. Ingest and scrape links
    scraped_links = []
    text_corpus = req.description or ""
    keywords = []
    
    for url in req.links or []:
        url_clean = url.strip()
        if not url_clean:
            continue
        link_id = add_event_link(event_id, url_clean)
        scrape_res = scrape_event_url(url_clean)
        update_event_link(
            link_id=link_id,
            title=scrape_res["title"],
            scraped_content=scrape_res["raw_text"],
            summary=scrape_res["summary"],
            status="scraped" if scrape_res["success"] else "partial"
        )
        scraped_links.append(scrape_res)
        text_corpus += " " + scrape_res["raw_text"]
        keywords.extend(scrape_res["keywords"])
        
    # 3. Autonomous Pre-Research Synthesis
    research = synthesize_research(
        event_title=req.title,
        category=req.category or "hackathon",
        deadline=req.deadline,
        links=scraped_links,
        user_notes=req.user_notes or ""
    )
    save_event_research(
        event_id=event_id,
        summary=research["summary"],
        key_deadlines=research["key_deadlines"],
        requirements=research["requirements"],
        tracks_or_prizes=research["tracks_or_prizes"],
        recommended_stack=research["recommended_stack"],
        clarification_questions=research["clarification_questions"]
    )
    
    # 4. Generate Phased Actionable Tasks
    phased_tasks = generate_phased_tasks(
        event_id=event_id,
        event_title=req.title,
        deadline_str=req.deadline,
        research_data=research,
        user_focus=req.user_focus or ""
    )
    for t in phased_tasks:
        create_task(
            event_id=event_id,
            title=t["title"],
            description=t["description"],
            phase=t["phase"],
            due_date=t["due_date"],
            priority=t["priority"],
            assigned_mcp=t["assigned_mcp"]
        )
        
    # 5. MCP Discovery & Auto-Configuration
    recommended_mcps = recommend_mcps_for_event(phased_tasks, keywords, text_corpus)
    for m in recommended_mcps:
        save_mcp_config(
            event_id=event_id,
            mcp_name=m["name"],
            description=m["description"],
            install_command=m["install_command"],
            config_json=m["config_json"]
        )
        
    # 6. Post initial non-nosy executive briefing
    ev_record = get_event(event_id)
    all_tasks = get_tasks(event_id)
    briefing = generate_non_nosy_briefing(ev_record, all_tasks)
    create_reminder(
        event_id=event_id,
        message=f"[{briefing['header']}] {briefing['message']}",
        severity=briefing["severity"]
    )
    
    return {
        "event_id": event_id,
        "event": ev_record,
        "research": research,
        "tasks": all_tasks,
        "mcps": recommended_mcps
    }

@app.get("/api/events/{event_id}")
def get_event_detail(event_id: int):
    event = get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    links = get_event_links(event_id)
    research = get_event_research(event_id)
    tasks = get_tasks(event_id)
    mcps = get_mcp_configs(event_id)
    
    # Calculate immediate briefing
    pending = [t for t in tasks if t["status"] != "done"]
    briefing = generate_non_nosy_briefing(event, pending)
    
    return {
        "event": event,
        "links": links,
        "research": research,
        "tasks": tasks,
        "mcps": mcps,
        "briefing": briefing
    }

@app.delete("/api/events/{event_id}")
def remove_event(event_id: int):
    delete_event(event_id)
    return {"status": "deleted", "event_id": event_id}

@app.post("/api/events/{event_id}/links")
def add_and_scrape_link(event_id: int, req: LinkAddRequest):
    event = get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    link_id = add_event_link(event_id, req.url, req.title or req.url)
    scrape_res = scrape_event_url(req.url)
    update_event_link(
        link_id=link_id,
        title=scrape_res["title"],
        scraped_content=scrape_res["raw_text"],
        summary=scrape_res["summary"],
        status="scraped" if scrape_res["success"] else "partial"
    )
    return {"status": "success", "link": scrape_res}

@app.post("/api/events/{event_id}/refine-tasks")
def refine_tasks_with_user_focus(event_id: int, req: ResearchRefineRequest):
    event = get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    research = get_event_research(event_id) or {}
    new_tasks = generate_phased_tasks(
        event_id=event_id,
        event_title=event["title"],
        deadline_str=event["deadline"],
        research_data=research,
        user_focus=req.user_focus
    )
    
    created = []
    for t in new_tasks:
        tid = create_task(
            event_id=event_id,
            title=t["title"],
            description=t["description"],
            phase=t["phase"],
            due_date=t["due_date"],
            priority=t["priority"],
            assigned_mcp=t["assigned_mcp"]
        )
        created.append(tid)
        
    return {"status": "success", "created_tasks": len(created)}

@app.get("/api/tasks")
def list_tasks(event_id: Optional[int] = Query(None)):
    return get_tasks(event_id)

@app.post("/api/tasks")
def add_custom_task(req: TaskCreateRequest):
    task_id = create_task(
        event_id=req.event_id,
        title=req.title,
        description=req.description or "",
        phase=req.phase or "Phase 1: Setup",
        due_date=req.due_date or "",
        priority=req.priority or "high",
        assigned_mcp=req.assigned_mcp or ""
    )
    return {"status": "created", "task_id": task_id}

@app.patch("/api/tasks/{task_id}/status")
def patch_task_status(task_id: int, req: TaskStatusUpdateRequest):
    update_task_status(task_id, req.status)
    return {"status": "updated", "task_id": task_id, "new_status": req.status}

@app.delete("/api/tasks/{task_id}")
def remove_task(task_id: int):
    delete_task(task_id)
    return {"status": "deleted", "task_id": task_id}

@app.get("/api/mcps")
def list_mcps(event_id: Optional[int] = Query(None)):
    return get_mcp_configs(event_id)

@app.patch("/api/mcps/{mcp_id}/toggle-install")
def toggle_mcp_installation(mcp_id: int):
    # Toggle installed bit
    configs = get_mcp_configs()
    target = next((c for c in configs if c["id"] == mcp_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="MCP config not found")
    new_state = 0 if target.get("is_installed", 0) else 1
    update_mcp_status(mcp_id, new_state)
    return {"status": "updated", "mcp_id": mcp_id, "is_installed": new_state}

@app.post("/api/mcps/export-config")
def export_mcp_configuration(event_id: Optional[int] = None):
    configs = get_mcp_configs(event_id)
    formatted_list = []
    for c in configs:
        formatted_list.append({
            "id": c["mcp_name"].lower().replace(" mcp", "").replace(" ", "-"),
            "command": c["config_json"].get("command", "npx") if isinstance(c["config_json"], dict) else "npx",
            "args": c["config_json"].get("args", []) if isinstance(c["config_json"], dict) else [],
            "env_required": list(c["config_json"].get("env", {}).keys()) if isinstance(c["config_json"], dict) else []
        })
    unified = generate_unified_config(formatted_list)
    filepath = save_mcp_config_to_disk(unified, "mcp_servers.json")
    return {"status": "exported", "filepath": filepath, "config": unified}

@app.get("/api/calendar")
def get_calendar_matrix():
    events = get_events()
    tasks = get_tasks()
    
    entries = []
    for ev in events:
        entries.append({
            "type": "event_deadline",
            "id": f"event-{ev['id']}",
            "title": f"[DEADLINE] {ev['title']}",
            "date": ev["deadline"],
            "category": ev.get("category", "hackathon"),
            "status": ev.get("status", "active")
        })
        
    for t in tasks:
        if t.get("due_date"):
            entries.append({
                "type": "task_due",
                "id": f"task-{t['id']}",
                "title": f"[MILESTONE] {t['title']}",
                "date": t["due_date"],
                "phase": t.get("phase", ""),
                "priority": t.get("priority", "high"),
                "status": t.get("status", "pending"),
                "assigned_mcp": t.get("assigned_mcp", "")
            })
            
    # Sort chronological
    entries.sort(key=lambda x: str(x.get("date", "")))
    return entries

@app.get("/api/reminders")
def list_reminders():
    return get_reminders(30)

@app.post("/api/reminders/mark-read")
def read_all_reminders():
    mark_reminders_read()
    return {"status": "marked_read"}

@app.get("/api/briefing")
def get_immediate_briefing():
    events = get_events()
    if not events:
        return {
            "header": "System Ready",
            "message": "No active events tracked. Ingest a hackathon or project link to initialize autonomous sentinel.",
            "severity": "info"
        }
    first_event = events[0]
    tasks = get_tasks(first_event["id"])
    pending = [t for t in tasks if t["status"] != "done"]
    return generate_non_nosy_briefing(first_event, pending)

# Chatbot Endpoints
class ChatMessageRequest(BaseModel):
    message: str

class ChannelCreateRequest(BaseModel):
    platform: str
    target: str
    webhook_url: Optional[str] = None
    api_token: Optional[str] = None

class ChannelTestRequest(BaseModel):
    channel_id: Optional[int] = None

@app.get("/api/chat/history")
def fetch_chat_history():
    from sentinel.db import get_chat_history
    history = get_chat_history(50)
    if not history:
        # Initial greeting if history is empty
        greeting = {
            "id": 0,
            "role": "assistant",
            "content": "Hello. I'm CHRONOS, your autonomous deadline sentinel.\n\nDrop your hackathon or project link, or tell me about an event. I'll navigate your links, extract critical criteria, ask you what you need, configure the necessary MCPs, and keep you ahead of your deadlines.",
            "card_type": None,
            "metadata": {},
            "created_at": ""
        }
        return [greeting]
    return history

@app.post("/api/chat")
def handle_chat_message(req: ChatMessageRequest):
    from sentinel.db import save_chat_message
    from sentinel.ai_engine import process_chat_turn
    
    # Save user message
    save_chat_message(role="user", content=req.message)
    
    # Process turn with progressive disclosure
    reply = process_chat_turn(req.message)
    
    # Save assistant message
    msg_id = save_chat_message(
        role="assistant",
        content=reply["content"],
        card_type=reply.get("card_type"),
        metadata=reply.get("metadata")
    )
    reply["id"] = msg_id
    return reply

@app.post("/api/chat/reset")
def reset_conversation():
    from sentinel.db import clear_chat_history
    clear_chat_history()
    return {"status": "cleared"}

# Multi-Platform Channels Endpoints (WhatsApp, Telegram, Discord, Slack)
@app.get("/api/channels")
def list_channels():
    from sentinel.db import get_notification_channels
    return get_notification_channels()

@app.post("/api/channels")
def add_channel(req: ChannelCreateRequest):
    from sentinel.db import save_notification_channel
    cid = save_notification_channel(
        platform=req.platform,
        target=req.target,
        webhook_url=req.webhook_url,
        api_token=req.api_token
    )
    return {"status": "created", "channel_id": cid}

@app.delete("/api/channels/{channel_id}")
def remove_channel(channel_id: int):
    from sentinel.db import delete_notification_channel
    delete_notification_channel(channel_id)
    return {"status": "deleted", "channel_id": channel_id}

@app.post("/api/channels/test")
def test_channel_ping(req: ChannelTestRequest):
    from sentinel.db import get_notification_channels
    from sentinel.channel_service import dispatch_to_channel
    
    channels = get_notification_channels()
    target_ch = next((c for c in channels if c["id"] == req.channel_id), None)
    if not target_ch:
        if channels:
            target_ch = channels[0]
        else:
            raise HTTPException(status_code=400, detail="No channels configured yet.")
            
    test_msg = f"[CHRONOS ALERT] Connected to {target_ch['platform'].upper()} ({target_ch['target']}). Executive briefings active."
    res = dispatch_to_channel(target_ch, test_msg)
    return res
