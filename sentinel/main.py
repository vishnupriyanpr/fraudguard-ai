"""
CHRONOS // FastAPI Server & Application Root
Local backend orchestrator connecting Link Scraper, Research Synthesizer,
Task Decomposer, MCP Integrator, Internal Calendar, and Executive Notifications.
"""

import os
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

from sentinel.db import (
    init_db, create_event, get_events, get_event, update_event, delete_event,
    add_event_link, update_event_link, get_event_links,
    save_event_research, get_event_research,
    create_task, get_tasks, update_task_status, update_task, get_task_stats, delete_task,
    save_mcp_config, get_mcp_configs, update_mcp_status,
    create_reminder, get_reminders, mark_reminders_read
)
from sentinel.integrations import gcal_connector, whatsapp_connector, agent_tool_builder
from sentinel.scraper import scrape_event_url
from sentinel.ai_engine import (
    synthesize_research, generate_phased_tasks, generate_non_nosy_briefing,
    get_active_model, get_active_provider, set_active_model, get_active_model_info,
    stream_llm
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

@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    # Prevent browser caching of any static or dynamic assets in development/production
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

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

class EventUpdateRequest(BaseModel):
    title: Optional[str] = None
    deadline: Optional[str] = None
    status: Optional[str] = None

class TaskCreateRequest(BaseModel):
    event_id: int
    title: str
    description: Optional[str] = ""
    phase: Optional[str] = "Phase 1: Setup"
    due_date: Optional[str] = ""
    priority: Optional[str] = "high"
    assigned_mcp: Optional[str] = ""

class TaskUpdateRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    phase: Optional[str] = "Phase 1: Setup"
    due_date: Optional[str] = ""
    priority: Optional[str] = "high"
    assigned_mcp: Optional[str] = ""

class TaskStatusUpdateRequest(BaseModel):
    status: str

class ToolTestRequest(BaseModel):
    parameters: Optional[dict] = {}

class WhatsAppSendRequest(BaseModel):
    recipient: Optional[str] = "+15550199"
    event_id: Optional[int] = None

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
        return FileResponse(
            index_file,
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"}
        )
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

@app.patch("/api/events/{event_id}")
def patch_event(event_id: int, req: EventUpdateRequest):
    event = get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    update_event(event_id, req.title, req.deadline, req.status)
    return {"status": "updated", "event": get_event(event_id)}

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

@app.get("/api/tasks/stats")
def fetch_task_stats(event_id: Optional[int] = Query(None)):
    return get_task_stats(event_id)

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

@app.put("/api/tasks/{task_id}")
def update_task_endpoint(task_id: int, req: TaskUpdateRequest):
    success = update_task(
        task_id=task_id,
        title=req.title,
        description=req.description or "",
        phase=req.phase or "Phase 1: Setup",
        due_date=req.due_date or "",
        priority=req.priority or "high",
        assigned_mcp=req.assigned_mcp or ""
    )
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "updated", "task_id": task_id}

@app.patch("/api/tasks/{task_id}/status")
def patch_task_status(task_id: int, req: TaskStatusUpdateRequest):
    update_task_status(task_id, req.status)
    return {"status": "updated", "task_id": task_id, "new_status": req.status}

@app.delete("/api/tasks/{task_id}")
def remove_task(task_id: int):
    delete_task(task_id)
    return {"status": "deleted", "task_id": task_id}

# ── Agent Tool Builder Endpoints (/agent-tool-builder compliant) ─────

@app.get("/api/tools/catalog")
def list_agent_tools():
    """Returns the comprehensive schema catalogue for all agent tools."""
    return agent_tool_builder.get_catalog()

@app.post("/api/tools/{tool_id}/test")
def test_agent_tool(tool_id: str, req: ToolTestRequest):
    """Executes a diagnostic test run for an Agent Tool with latency & stdout metrics."""
    res = agent_tool_builder.execute_tool_test(tool_id, req.parameters)
    return res

# ── Integrations: Google Calendar & WhatsApp Cloud ──────────────────

@app.get("/api/integrations/status")
def get_all_integrations_status():
    """Returns status of external connectors."""
    return {
        "google_calendar": gcal_connector.get_status(),
        "whatsapp": whatsapp_connector.get_status()
    }

@app.post("/api/integrations/google-calendar/sync")
def sync_google_calendar(event_id: Optional[int] = Query(None)):
    """Synchronizes tasks & milestones for an event to Google Calendar."""
    events = get_events()
    target_event = None
    if event_id:
        target_event = get_event(event_id)
    elif events:
        target_event = events[0]
        
    if not target_event:
        raise HTTPException(status_code=400, detail="No active event found to synchronize.")
        
    tasks = get_tasks(target_event["id"])
    result = gcal_connector.sync_milestones(target_event["title"], tasks)
    return result

@app.post("/api/integrations/whatsapp/send")
def send_whatsapp_digest(req: WhatsAppSendRequest):
    """Dispatches real-time executive WhatsApp briefing to designated phone."""
    events = get_events()
    target_event = None
    if req.event_id:
        target_event = get_event(req.event_id)
    elif events:
        target_event = events[0]
        
    if not target_event:
        raise HTTPException(status_code=400, detail="No active event found to send briefing for.")
        
    tasks = get_tasks(target_event["id"])
    pending = [t for t in tasks if t.get("status") != "done"]
    res = whatsapp_connector.send_executive_briefing(
        recipient=req.recipient or "+15550199",
        title=target_event["title"],
        deadline=target_event["deadline"],
        pending_tasks=pending
    )
    return res

@app.get("/api/webhook/whatsapp")
def verify_whatsapp_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge")
):
    """Meta webhook verification endpoint."""
    challenge = whatsapp_connector.verify_webhook(hub_mode, hub_verify_token, hub_challenge)
    if challenge:
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(content=challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Verification token mismatch")

@app.post("/api/webhook/whatsapp")
async def handle_whatsapp_webhook(request: Request):
    """Meta incoming WhatsApp message / event receiver."""
    body = await request.json()
    return {"status": "received", "data": body}

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
            "event_id": ev["id"],
            "title": ev["title"],
            "description": ev.get("description", ""),
            "date": ev["deadline"],
            "category": ev.get("category", "hackathon"),
            "status": ev.get("status", "active")
        })
        
    for t in tasks:
        if t.get("due_date"):
            entries.append({
                "type": "task_due",
                "id": f"task-{t['id']}",
                "task_id": t["id"],
                "event_id": t.get("event_id"),
                "title": t["title"].replace("[MILESTONE] ", ""),
                "description": t.get("description", ""),
                "date": t["due_date"],
                "phase": t.get("phase", "Phase 1: Setup"),
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

# ── Model Switcher API (Ollama Local + Groq Cloud LPU) ────────────────

class ModelSwitchRequest(BaseModel):
    model: str
    provider: Optional[str] = None

@app.get("/api/models")
def list_available_models():
    """Returns available local Ollama models and Groq cloud models."""
    import requests as _req
    models = []
    
    # 1. Local Ollama models
    try:
        resp = _req.get("http://localhost:11434/api/tags", timeout=3)
        if resp.status_code == 200:
            raw = resp.json().get("models", [])
            for m in raw:
                name = m.get("name", "")
                models.append({
                    "id": name,
                    "name": name,
                    "provider": "ollama",
                    "badge": "Ollama Local",
                    "size": m.get("size", 0)
                })
    except Exception:
        # Fallback offline defaults for Ollama if daemon starting
        for fallback_name in ["qwen3.5:9b", "qwen2.5:3b", "gemma4:e2b"]:
            models.append({
                "id": fallback_name,
                "name": fallback_name,
                "provider": "ollama",
                "badge": "Ollama Local",
                "size": 0
            })

    # 2. Cloud Groq LPU models (if API key present)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and not "your_" in groq_key.lower():
        models.extend([
            {
                "id": "openai/gpt-oss-20b",
                "name": "gpt-oss-20b",
                "provider": "groq",
                "badge": "Groq Fast LPU",
                "size": 0
            },
            {
                "id": "qwen/qwen3.8-27b",
                "name": "qwen3.8-27b",
                "provider": "groq",
                "badge": "Groq Frontier LPU",
                "size": 0
            },
            {
                "id": "openai/gpt-oss-120b",
                "name": "gpt-oss-120b",
                "provider": "groq",
                "badge": "Groq Deep LPU",
                "size": 0
            }
        ])

    return models

@app.get("/api/models/active")
def get_active_model_endpoint():
    """Returns the currently selected model and provider."""
    return get_active_model_info()

@app.post("/api/models/switch")
def switch_active_model(req: ModelSwitchRequest):
    """Switches the active model and provider."""
    info = set_active_model(req.model, req.provider)
    return {"status": "switched", **info}

@app.get("/api/models/status")
def get_model_status():
    """Checks online/offline status of the active provider."""
    import requests as _req
    provider = get_active_provider()
    model = get_active_model()
    
    if provider == "groq":
        key = os.getenv("GROQ_API_KEY")
        if key:
            try:
                resp = _req.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {key}"}, timeout=3)
                if resp.status_code == 200:
                    return {"status": "online", "model": model, "provider": "groq"}
            except Exception:
                pass
        return {"status": "offline", "model": model, "provider": "groq"}
    else:
        try:
            resp = _req.get("http://localhost:11434/api/tags", timeout=2)
            if resp.status_code == 200:
                return {"status": "online", "model": model, "provider": "ollama"}
        except Exception:
            pass
        return {"status": "offline", "model": model, "provider": "ollama"}

# ── Streaming Chat (SSE) ────────────────────────────────────────────

class StreamChatRequest(BaseModel):
    message: str

@app.post("/api/chat/stream")
def stream_chat(req: StreamChatRequest):
    """
    Streams LLM tokens via Server-Sent Events using stream_llm.
    Each frame is: data: {"token": "..."} or data: {"reasoning": "..."}
    """
    import json as _json
    from sentinel.db import save_chat_message

    def _generate():
        # Save user message
        save_chat_message(role="user", content=req.message)
        
        system_prompt = (
            "You are CHRONOS, an expert autonomous deadline sentinel and hackathon architect. "
            "Help the user stay ahead of milestones with concise, razor-sharp advice."
        )
        full_content = []
        try:
            for chunk in stream_llm(system_prompt, req.message):
                if "reasoning" in chunk:
                    yield f"data: {_json.dumps({'reasoning': chunk['reasoning']})}\n\n"
                if "token" in chunk:
                    full_content.append(chunk["token"])
                    yield f"data: {_json.dumps({'token': chunk['token']})}\n\n"
            
            # Save assistant reply
            final_text = "".join(full_content)
            if final_text:
                save_chat_message(role="assistant", content=final_text)
                
            yield "data: [DONE]\n\n"
        except Exception as exc:
            yield f"data: {_json.dumps({'error': str(exc)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(_generate(), media_type="text/event-stream")

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
