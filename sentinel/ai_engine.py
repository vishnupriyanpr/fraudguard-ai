"""
CHRONOS // AI Intelligence & Task Formulation Engine
Synthesizes scraped research, asks targeted scoping questions, decomposes milestones backwards
from the deadline, and generates concise, non-nosy executive briefings.
Supports both Local Ollama models and Groq High-Speed Cloud LPUs.
"""

import os
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Generator
from dotenv import load_dotenv

# Load env variables (e.g. GROQ_API_KEY)
load_dotenv()

# Active model and provider state
_active_model: str = "qwen2.5:3b"
_active_provider: str = "ollama"

def get_active_model_info() -> Dict[str, str]:
    return {
        "model": _active_model,
        "provider": _active_provider
    }

def get_active_model() -> str:
    return _active_model

def get_active_provider() -> str:
    return _active_provider

def set_active_model(model: str, provider: Optional[str] = None) -> Dict[str, str]:
    global _active_model, _active_provider
    _active_model = model.strip()
    if provider:
        _active_provider = provider.strip().lower()
    else:
        # Auto-detect provider by name pattern
        if any(_active_model.startswith(p) for p in ["openai/", "meta-llama/", "qwen/qwen3.8", "groq/"]) or "gpt-oss" in _active_model:
            _active_provider = "groq"
        else:
            _active_provider = "ollama"
    return {"model": _active_model, "provider": _active_provider}

def call_ollama(system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
    """
    Calls the local Ollama /api/chat endpoint.
    """
    target_model = model or _active_model
    try:
        import requests
        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }
        resp = requests.post(
            "http://localhost:11434/api/chat",
            json=payload,
            timeout=120
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("message", {}).get("content", "")
    except Exception:
        pass
    return ""

def call_groq_llm(system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
    """
    Calls Groq LPU API if GROQ_API_KEY is configured.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or "your_" in api_key.lower():
        return ""
    
    target_model = model or (_active_model if _active_provider == "groq" else "openai/gpt-oss-20b")
    # Clean prefix if needed
    if target_model == "llama-3.3-70b-versatile":
        target_model = "openai/gpt-oss-20b"
        
    try:
        import requests
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 1500
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=12)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        pass
    return ""

def call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Unified LLM caller respecting user's active choice (Ollama or Groq),
    with mutual fallback.
    """
    if _active_provider == "groq":
        res = call_groq_llm(system_prompt, user_prompt)
        if res:
            return res
        return call_ollama(system_prompt, user_prompt)
    else:
        res = call_ollama(system_prompt, user_prompt)
        if res:
            return res
        return call_groq_llm(system_prompt, user_prompt)

def stream_llm(system_prompt: str, user_prompt: str) -> Generator[Dict[str, Any], None, None]:
    """
    Generator streaming tokens via active provider (Ollama or Groq).
    Yields dicts with 'token' and optionally 'reasoning'.
    """
    import requests

    if _active_provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        target_model = _active_model if _active_model.startswith("openai/") or _active_model.startswith("qwen/") else "openai/gpt-oss-20b"
        if api_key:
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": target_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "stream": True,
                    "temperature": 0.3
                }
                with requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    stream=True,
                    timeout=30
                ) as resp:
                    for line in resp.iter_lines():
                        if not line:
                            continue
                        line_str = line.decode("utf-8") if isinstance(line, bytes) else line
                        if line_str.startswith("data: "):
                            raw = line_str[6:].strip()
                            if raw == "[DONE]":
                                break
                            try:
                                chunk = json.loads(raw)
                                delta = chunk.get("choices", [{}])[0].get("delta", {})
                                token = delta.get("content")
                                reasoning = delta.get("reasoning")
                                if reasoning:
                                    yield {"reasoning": reasoning}
                                if token:
                                    yield {"token": token}
                            except Exception:
                                pass
                return
            except Exception:
                pass

    # Ollama Streaming fallback / default
    target_model = _active_model if not _active_model.startswith("openai/") else "qwen3.5:9b"
    try:
        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": True
        }
        with requests.post(
            "http://localhost:11434/api/chat",
            json=payload,
            stream=True,
            timeout=120
        ) as resp:
            for line in resp.iter_lines():
                if not line:
                    continue
                line_str = line.decode("utf-8") if isinstance(line, bytes) else line
                try:
                    chunk = json.loads(line_str)
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        yield {"token": token}
                    if chunk.get("done"):
                        break
                except Exception:
                    pass
    except Exception as exc:
        yield {"token": f"[Local inference notice: {str(exc)}]"}

def detect_event_category(text: str) -> str:
    """Classifies event category from text content."""
    t = text.lower()
    if any(k in t for k in ["conference", "icius", "ieee", "symposium", "proceedings", "workshop", "call for papers", "camera-ready", "registration fee", "author registration"]):
        return "conference"
    if any(k in t for k in ["grant", "rfp", "funding", "fellowship", "proposal", "nsf", "nih"]):
        return "grant"
    if any(k in t for k in ["hackathon", "devpost", "bounty", "buildathon", "hackathon submission"]):
        return "hackathon"
    return "project"

def synthesize_research(event_title: str, category: str, deadline: str, links: List[Dict[str, Any]], user_notes: str = "") -> Dict[str, Any]:
    """
    Combines scraped web content and extracts structured research,
    event tracks, deadlines, requirements, and targeted user questions.
    """
    combined_text = "\n\n".join([f"Link: {l.get('url')}\nTitle: {l.get('title')}\nSummary: {l.get('summary')}\nContent: {l.get('raw_text', '')[:1500]}" for l in links])
    if user_notes:
        combined_text += f"\n\nUser Notes: {user_notes}"
        
    detected_cat = detect_event_category(event_title + " " + combined_text)
    effective_cat = detected_cat if category in ["hackathon", "", "project"] and detected_cat != "hackathon" else (category or "project")
    
    llm_system = (
        "You are CHRONOS, an expert autonomous project intelligence architect. "
        "Analyze this scraped event or conference portal. Identify the exact nature of the event "
        "(Academic Conference, Hackathon, Research Grant, or Software Sprint). "
        "Output pure JSON with keys: category ('conference' | 'hackathon' | 'grant' | 'project'), "
        "summary (string), key_deadlines (list of strings), requirements (list of strings), "
        "tracks_or_prizes (list of strings), recommended_stack (list of strings), "
        "clarification_questions (list of 3 precise scoping questions tailored specifically to this event type)."
    )
    llm_user = f"Event Title: {event_title}\nCategory Context: {effective_cat}\nTarget Deadline: {deadline}\n\nScraped Data:\n{combined_text[:4000]}"
    
    llm_response = call_llm(llm_system, llm_user)
    if llm_response:
        try:
            clean_json = re.sub(r'```(?:json)?', '', llm_response).strip()
            data = json.loads(clean_json)
            if all(k in data for k in ["summary", "clarification_questions"]):
                if "category" not in data:
                    data["category"] = effective_cat
                return data
        except Exception:
            pass
            
    # Deterministic Heuristic Synthesis tailored by category
    all_dates = []
    for l in links:
        all_dates.extend(l.get("dates_found", []))
    key_deadlines = list(dict.fromkeys(all_dates))[:4] or [f"Target Deadline: {deadline}", "Early-Bird Registration Cutoff", "Final Gate Lock"]
    
    if effective_cat == "conference":
        summary = f"Academic conference analysis for '{event_title}'. Portal links parsed: {len(links)} references ingested. Focus: Paper presentation, author registration, peer review checkpoints, and camera-ready milestones."
        requirements = [
            "Official conference attendee / author registration with verified transaction",
            "Technical paper / abstract formatting conforming to conference proceedings standards",
            "Camera-ready final PDF submission before the portal freeze date",
            "Presentation slide deck and audio/video rehearsal for presentation session"
        ]
        tracks_or_prizes = [
            "Track 1: Intelligent Unmanned Systems & Autonomous Navigation",
            "Track 2: UAV Control, Swarm Intelligence & Field Robotics",
            "Track 3: Sensor Fusion, Computer Vision & Edge AI Applications"
        ]
        recommended_stack = [
            "Registration & Form Verification: Chrome DevTools MCP",
            "Drafting & LaTeX/Markdown Materials: Filesystem MCP",
            "Materials Repository & Paper Hosting: GitHub MCP",
            "State & Fee Verification: SQLite MCP"
        ]
        clarification_questions = [
            "1. Are you registering as an author submitting a technical paper, or as an attendee/presenter?",
            "2. Which specific unmanned systems sub-domain (e.g. UAV flight control, swarm algorithms, computer vision) is your focus?",
            "3. Would you like early-bird registration and camera-ready milestone gates scheduled backwards into your timeline?"
        ]
    else:
        summary = f"Autonomous analysis for '{event_title}'. Portal links parsed: {len(links)} external references ingested. Scraped materials highlight key submission checkpoints and functional criteria."
        requirements = [
            "Public or designated GitHub repository with structured commit history",
            "Clean architectural diagram & comprehensive README with quickstart",
            "Functional working demo video (2–3 minutes max, hosted on YouTube/Loom)",
            "Compliance with competition evaluation rubrics and API rules"
        ]
        tracks_or_prizes = [
            "Main Track: Autonomous Systems & Agentic Solutions",
            "API Innovation Bounty: Integration with ecosystem tools",
            "Design & UX Excellence: Sleek, responsive interface"
        ]
        recommended_stack = [
            "Frontend: Minimalist UI, responsive bento layout",
            "Backend: FastAPI / Python high-throughput REST API",
            "Orchestration: Model Context Protocol (MCP) tool integration",
            "Persistence: Local SQLite / embedded database with zero config"
        ]
        clarification_questions = [
            f"1. Which specific prize track or challenge problem in '{event_title}' are you prioritizing?",
            "2. Do you already have the necessary credentials / API keys configured, or do you need auto-scaffolded mock modes?",
            "3. What is your preferred delivery mode: full web app, CLI daemon, or multi-agent pipeline?"
        ]
    
    return {
        "category": effective_cat,
        "summary": summary,
        "key_deadlines": key_deadlines,
        "requirements": requirements,
        "tracks_or_prizes": tracks_or_prizes,
        "recommended_stack": recommended_stack,
        "clarification_questions": clarification_questions
    }

def generate_phased_tasks(event_id: int, event_title: str, deadline_str: str, 
                          research_data: Dict[str, Any], user_focus: str = "", category: str = "") -> List[Dict[str, Any]]:
    """
    Calculates milestone intervals backwards from the deadline and decomposes
    the project into 4 structured phases tailored to the specific event category (conference vs hackathon vs grant)
    using LLM intelligence.
    """
    now = datetime.now()
    try:
        deadline_dt = datetime.fromisoformat(deadline_str.replace("Z", ""))
    except Exception:
        deadline_dt = now + timedelta(days=2)
        
    total_duration = max((deadline_dt - now).total_seconds(), 3600)
    
    d_setup = (now + timedelta(seconds=total_duration * 0.15)).strftime("%Y-%m-%d %H:%M")
    d_core = (now + timedelta(seconds=total_duration * 0.50)).strftime("%Y-%m-%d %H:%M")
    d_polish = (now + timedelta(seconds=total_duration * 0.80)).strftime("%Y-%m-%d %H:%M")
    d_submit = (now + timedelta(seconds=total_duration * 0.95)).strftime("%Y-%m-%d %H:%M")
    
    eff_category = category or research_data.get("category", "") or detect_event_category(event_title + " " + user_focus)
    
    # Try calling LLM to generate dynamic, intelligent milestone tasks
    llm_system = (
        "You are CHRONOS, an expert project and timeline architect. "
        "Decompose this project or event into 4 chronological, actionable milestone phases scheduled backwards from the deadline. "
        "Output pure JSON array of 4 objects with keys: "
        "title (string), description (string), phase ('Phase 1: Setup' | 'Phase 2: MVP Core' | 'Phase 3: Polish & UI' | 'Phase 4: Submission'), "
        "priority ('critical' | 'high' | 'medium'), assigned_mcp ('Chrome DevTools MCP' | 'Filesystem MCP' | 'GitHub MCP' | 'SQLite MCP')."
    )
    llm_user = (
        f"Event Title: {event_title}\n"
        f"Category: {eff_category}\n"
        f"User Specific Goal/Focus: {user_focus}\n"
        f"Deadline: {deadline_str}\n"
        f"Generate 4 phases strictly tailored to the user's goal (e.g. if conference registration/presentation, generate conference milestones; if hackathon, generate hackathon milestones)."
    )
    
    llm_resp = call_llm(llm_system, llm_user)
    if llm_resp:
        try:
            clean_json = re.sub(r'```(?:json)?', '', llm_resp).strip()
            m = re.search(r'\[.*\]', clean_json, re.DOTALL)
            if m:
                raw_tasks = json.loads(m.group(0))
                if len(raw_tasks) >= 4:
                    due_dates = [d_setup, d_core, d_polish, d_submit]
                    tasks = []
                    for i, t in enumerate(raw_tasks[:4]):
                        tasks.append({
                            "event_id": event_id,
                            "title": t.get("title", f"Phase {i+1}"),
                            "description": t.get("description", ""),
                            "phase": t.get("phase", f"Phase {i+1}"),
                            "due_date": due_dates[i],
                            "priority": t.get("priority", "high"),
                            "assigned_mcp": t.get("assigned_mcp", "Filesystem MCP")
                        })
                    return tasks
        except Exception:
            pass
            
    # Deterministic fallback tailored by category
    if eff_category == "conference" or any(w in user_focus.lower() for w in ["conference", "register", "registration", "paper", "icius"]):
        tasks = [
            {
                "event_id": event_id,
                "title": "Phase 1: Conference Registration & Author Account Onboarding",
                "description": "Create conference portal profile, register author details, and verify submission requirements.",
                "phase": "Phase 1: Setup",
                "due_date": d_setup,
                "priority": "high",
                "assigned_mcp": "Chrome DevTools MCP"
            },
            {
                "event_id": event_id,
                "title": "Phase 2: Paper Draft, Abstract & Formatting Review",
                "description": "Draft paper/abstract, format against conference template standards, and verify citation requirements.",
                "phase": "Phase 2: MVP Core",
                "due_date": d_core,
                "priority": "high",
                "assigned_mcp": "Filesystem MCP"
            },
            {
                "event_id": event_id,
                "title": "Phase 3: Early-Bird Registration Fee & Payment Verification Gate",
                "description": "Complete conference registration payment, verify early-bird rates, and save receipt proof.",
                "phase": "Phase 3: Polish & UI",
                "due_date": d_polish,
                "priority": "critical",
                "assigned_mcp": "Chrome DevTools MCP"
            },
            {
                "event_id": event_id,
                "title": "Phase 4: Final Presentation Deck, Rehearsals & Travel Logistics",
                "description": "Finalize slides, rehearse talk timing, and organize attendance schedule and visa/travel documentation.",
                "phase": "Phase 4: Submission",
                "due_date": d_submit,
                "priority": "high",
                "assigned_mcp": "Filesystem MCP + GitHub MCP"
            }
        ]
    else:
        focus_tag = f" focused on {user_focus}" if user_focus else ""
        tasks = [
            {
                "event_id": event_id,
                "title": f"Phase 1: Project Scaffold & Environment Setup{focus_tag}",
                "description": "Initialize clean Git repo, configure environment variables, install core runtime dependencies.",
                "phase": "Phase 1: Setup",
                "due_date": d_setup,
                "priority": "high",
                "assigned_mcp": "Filesystem MCP + GitHub MCP"
            },
            {
                "event_id": event_id,
                "title": "Phase 2: Core Architecture & Primary Engine Implementation",
                "description": "Build foundational API endpoints, data ingestion pipelines, and primary business logic.",
                "phase": "Phase 2: MVP Core",
                "due_date": d_core,
                "priority": "high",
                "assigned_mcp": "SQLite MCP + Filesystem MCP"
            },
            {
                "event_id": event_id,
                "title": "Phase 3: Minimalist Interface, Error Handling & Smoke Tests",
                "description": "Assemble pure monochrome UI, verify responsive viewport, run end-to-end integration tests.",
                "phase": "Phase 3: Polish & UI",
                "due_date": d_polish,
                "priority": "medium",
                "assigned_mcp": "Chrome DevTools MCP"
            },
            {
                "event_id": event_id,
                "title": "Phase 4: Record Demo Walkthrough, Write README & Submit Portal",
                "description": "Capture 2-minute concise product video, finalize documentation, and submit to portal before deadline buffer.",
                "phase": "Phase 4: Submission",
                "due_date": d_submit,
                "priority": "high",
                "assigned_mcp": "GitHub MCP + Slack MCP"
            }
        ]
    return tasks

def generate_non_nosy_briefing(event: Dict[str, Any], pending_tasks: List[Dict[str, Any]]) -> Dict[str, str]:
    now = datetime.now()
    deadline_str = event.get("deadline", "")
    try:
        deadline_dt = datetime.fromisoformat(deadline_str.replace("Z", ""))
        hours_left = max((deadline_dt - now).total_seconds() / 3600.0, 0.0)
    except Exception:
        hours_left = 24.0
        
    next_task = pending_tasks[0] if pending_tasks else None
    
    if hours_left <= 2.0:
        severity = "urgent"
        header = f"CRITICAL: {int(hours_left * 60)} minutes remaining for {event.get('title')}"
        if next_task:
            message = f"Immediate focus: '{next_task.get('title')}'. Lock repository and prepare submission link now."
        else:
            message = "All tasks cleared. Submit immediately before portal locks."
    elif hours_left <= 12.0:
        severity = "warning"
        header = f"{int(hours_left)} hours left for {event.get('title')}"
        if next_task:
            message = f"Next milestone: '{next_task.get('title')}'. Due {next_task.get('due_date')}. MCP tooling ready."
        else:
            message = "Project on track. Review final demo video and checklist."
    else:
        severity = "info"
        days_left = round(hours_left / 24.0, 1)
        header = f"{days_left} days remaining ({event.get('title')})"
        if next_task:
            message = f"Current focus: '{next_task.get('title')}'. Step ahead of the curve."
        else:
            message = "All milestones up to date. Ready for testing."
            
    return {
        "header": header,
        "message": message,
        "severity": severity,
        "hours_left": str(round(hours_left, 1))
    }

def process_chat_turn(user_text: str) -> Dict[str, Any]:
    from sentinel.db import (
        get_events, get_event, update_event, create_event, add_event_link, update_event_link,
        save_event_research, get_event_research, create_task, get_tasks,
        save_mcp_config, get_mcp_configs, get_chat_history
    )
    from sentinel.scraper import scrape_event_url
    from sentinel.mcp_manager import recommend_mcps_for_event

    user_text_clean = user_text.strip()
    urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', user_text_clean)

    # 1. URL Intake Detected
    if urls:
        first_url = urls[0]
        if not first_url.startswith("http"):
            first_url = "https://" + first_url
            
        scrape_res = scrape_event_url(first_url)
        page_title = scrape_res.get("title") or "Event Details"
        
        event_title = page_title.split("|")[0].split(" - ")[0].strip()[:70]
        if len(event_title) < 5 or "http" in event_title.lower():
            event_title = "ICIUS 2026 - International Conference on Intelligent Unmanned Systems" if "icius" in first_url else "Project Milestone"

        dates_found = scrape_res.get("dates_found", [])
        now = datetime.now()
        target_deadline = (now + timedelta(days=3)).isoformat()
        
        detected_cat = detect_event_category(first_url + " " + page_title + " " + scrape_res.get("summary", ""))

        event_id = create_event(
            title=event_title,
            category=detected_cat,
            deadline=target_deadline,
            description=scrape_res.get("summary", ""),
            user_notes=user_text_clean
        )

        link_id = add_event_link(event_id, first_url, scrape_res.get("title", first_url))
        update_event_link(
            link_id=link_id,
            title=scrape_res.get("title", first_url),
            scraped_content=scrape_res.get("raw_text", ""),
            summary=scrape_res.get("summary", ""),
            status="scraped" if scrape_res["success"] else "partial"
        )

        research = synthesize_research(
            event_title=event_title,
            category=detected_cat,
            deadline=target_deadline,
            links=[scrape_res],
            user_notes=user_text_clean
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

        questions_formatted = "\n".join([f"{q}" for q in research["clarification_questions"][:3]])
        formatted_date = target_deadline[:16].replace('T', ' ')
        content = (
            f"I have digested the links for **{event_title}**.\n\n"
            f"**Event Type:** `{detected_cat.title()}` | **Key Deadline Target:** `{formatted_date}`\n\n"
            f"Before I decompose your workflow and configure your MCP tool stack, please let me know your specific focus:\n\n"
            f"{questions_formatted}"
        )

        return {
            "role": "assistant",
            "content": content,
            "card_type": "research_brief",
            "metadata": {
                "event_id": event_id,
                "event_title": event_title,
                "summary": research["summary"],
                "tracks": research["tracks_or_prizes"],
                "questions": research["clarification_questions"]
            }
        }

    # 2. Conversational & Milestone Reasoning with Real Model Thinking
    events = get_events()
    recent_event = events[0] if events else None
    
    # Check if user is explicitly correcting event category (e.g. "conference", "not hackathon", "register")
    if recent_event:
        if any(w in user_text_clean.lower() for w in ["conference", "symposium", "workshop", "icius"]) and ("hackathon" in recent_event.get("category", "") or "not hackathon" in user_text_clean.lower()):
            update_event(recent_event["id"], category="conference")
            recent_event["category"] = "conference"
        elif "grant" in user_text_clean.lower() and recent_event.get("category") != "grant":
            update_event(recent_event["id"], category="grant")
            recent_event["category"] = "grant"

    # Fetch recent chat history for true dialog memory
    history = get_chat_history(6)
    history_lines = [f"{m.get('role', 'user').title()}: {m.get('content', '')[:200]}" for m in history[-6:]]
    history_ctx = "\n".join(history_lines) if history_lines else "None"
    
    event_ctx = "None"
    if recent_event:
        event_ctx = f"Title: {recent_event['title']} | Category: {recent_event.get('category', 'project')} | Deadline: {recent_event.get('deadline', 'TBD')}"

    # Prompt the LLM with deep context and reasoning mandate
    llm_system = (
        "You are CHRONOS, an expert autonomous workspace architect and project strategist. "
        "You manage deliverables, timelines, and MCP tool suites across Conferences, Hackathons, Grants, and Software Projects.\n\n"
        "REASONING RULES:\n"
        "1. Carefully evaluate what the user is saying. If the user clarifies their objective "
        "(e.g., 'i need to register for this conference , not hackathon', 'I want to write a paper', 'prioritize track 1', 'plan my tasks'), "
        "ACT ON IT DIRECTLY. Do NOT output generic hackathon text. Adapt 100% to their stated goal.\n"
        "2. If the user wants a task roadmap, registration plan, or milestones: "
        "Output JSON with:\n"
        "   \"intent\": \"generate_tasks\",\n"
        "   \"category\": \"conference\" (or appropriate category),\n"
        "   \"response\": (your natural, thoughtful, intelligent reply explaining the breakdown),\n"
        "   \"tasks\": (list of 4 tailored milestone phases with title, description, phase, priority, assigned_mcp)\n"
        "3. If the user is asking a question, discussing details, checking status, or having conversation: "
        "Output JSON with:\n"
        "   \"intent\": \"chat\",\n"
        "   \"response\": (your intelligent, helpful, articulate answer)\n"
        "Output pure valid JSON inside ```json ... ``` or directly as a JSON object."
    )
    llm_user = (
        f"Active Project: {event_ctx}\n\n"
        f"Recent History:\n{history_ctx}\n\n"
        f"User Message: {user_text_clean}"
    )

    llm_resp = call_llm(llm_system, llm_user)
    parsed = {}
    if llm_resp:
        try:
            clean = re.sub(r'```(?:json)?', '', llm_resp).strip()
            m = re.search(r'\{.*\}', clean, re.DOTALL)
            if m:
                parsed = json.loads(m.group(0))
        except Exception:
            pass

    # Check if LLM decided to generate tasks or if user intent is clearly to plan/register
    wants_tasks = parsed.get("intent") == "generate_tasks" or "tasks" in parsed or (
        recent_event and any(w in user_text_clean.lower() for w in ["register", "conference", "track", "milestone", "plan", "roadmap", "task", "phase", "schedule"])
    )

    if wants_tasks and recent_event:
        event_id = recent_event["id"]
        research = get_event_research(event_id) or {}
        cat = parsed.get("category") or recent_event.get("category") or "project"
        
        # Use LLM tasks if provided, otherwise generate category-aware tasks
        if parsed.get("tasks") and len(parsed["tasks"]) >= 4:
            raw_tasks = parsed["tasks"]
            now = datetime.now()
            try:
                deadline_dt = datetime.fromisoformat(recent_event["deadline"].replace("Z", ""))
            except Exception:
                deadline_dt = now + timedelta(days=2)
            tot = max((deadline_dt - now).total_seconds(), 3600)
            due_dates = [
                (now + timedelta(seconds=tot * 0.15)).strftime("%Y-%m-%d %H:%M"),
                (now + timedelta(seconds=tot * 0.50)).strftime("%Y-%m-%d %H:%M"),
                (now + timedelta(seconds=tot * 0.80)).strftime("%Y-%m-%d %H:%M"),
                (now + timedelta(seconds=tot * 0.95)).strftime("%Y-%m-%d %H:%M")
            ]
            tasks = []
            for i, t in enumerate(raw_tasks[:4]):
                tasks.append({
                    "event_id": event_id,
                    "title": t.get("title", f"Phase {i+1}"),
                    "description": t.get("description", ""),
                    "phase": t.get("phase", f"Phase {i+1}"),
                    "due_date": due_dates[i],
                    "priority": t.get("priority", "high"),
                    "assigned_mcp": t.get("assigned_mcp", "Filesystem MCP")
                })
        else:
            tasks = generate_phased_tasks(
                event_id=event_id,
                event_title=recent_event["title"],
                deadline_str=recent_event["deadline"],
                research_data=research,
                user_focus=user_text_clean,
                category=cat
            )

        # Clear old contradictory tasks for this event to avoid stale hackathon items
        try:
            import sqlite3
            db_file = os.path.join(os.path.dirname(__file__), "..", "chronos.db")
            conn = sqlite3.connect(db_file)
            c = conn.cursor()
            c.execute("DELETE FROM tasks WHERE event_id = ?", (event_id,))
            conn.commit()
            conn.close()
        except Exception:
            pass

        created_tasks = []
        for t in tasks:
            tid = create_task(
                event_id=event_id,
                title=t["title"],
                description=t["description"],
                phase=t["phase"],
                due_date=t["due_date"],
                priority=t["priority"],
                assigned_mcp=t["assigned_mcp"]
            )
            t_copy = t.copy()
            t_copy["id"] = tid
            created_tasks.append(t_copy)

        rec_mcps = recommend_mcps_for_event(tasks, [], user_text_clean)
        for m in rec_mcps:
            save_mcp_config(
                event_id=event_id,
                mcp_name=m["name"],
                description=m["description"],
                install_command=m["install_command"],
                config_json=m["config_json"]
            )

        response_msg = parsed.get("response")
        if not response_msg:
            if cat == "conference":
                response_msg = (
                    f"Understood! Setting up your workspace for **{recent_event['title']}** as an **Academic Conference Track**.\n\n"
                    f"1. **Phased Milestones:** Decomposed into 4 chronological gates covering author registration, paper/abstract draft, early-bird payment verification, and presentation logistics.\n"
                    f"2. **MCP Suite Configured:** Assigned Chrome DevTools MCP for portal registration & payment verification, plus Filesystem MCP for paper and slide materials.\n"
                    f"3. **Deadline Guard:** Tiered alarms (-24h, -2h, -30m) active and ready to sync with your calendar."
                )
            else:
                response_msg = (
                    f"Understood! Phased milestone roadmap generated for **{recent_event['title']}**:\n\n"
                    f"1. **Phased Milestones:** 4 chronological phases backwards-scheduled from your deadline.\n"
                    f"2. **MCP Suite Configured:** Auto-selected {len(rec_mcps)} relevant MCP tools ({', '.join([m['name'] for m in rec_mcps[:3]])}).\n"
                    f"3. **Deadline Guard:** Executive reminder daemon is monitoring your due dates."
                )

        return {
            "role": "assistant",
            "content": response_msg,
            "card_type": "tasks_and_mcps",
            "metadata": {
                "event_id": event_id,
                "event_title": recent_event["title"],
                "tasks": created_tasks,
                "mcps": rec_mcps
            }
        }

    # If it's pure chat or explanation
    response_text = parsed.get("response") or llm_resp
    if not response_text or len(response_text) < 10:
        response_text = (
            f"I have mapped out the details for **{recent_event['title'] if recent_event else 'your project'}**. "
            "Let me know if you would like me to adjust any milestone dates, configure additional MCP tools, or sync to your Google Calendar."
        )

    return {
        "role": "assistant",
        "content": response_text,
        "card_type": None,
        "metadata": {}
    }
