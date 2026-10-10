"""
CHRONOS // AI Intelligence & Task Formulation Engine
Synthesizes scraped research, asks targeted scoping questions, decomposes milestones backwards
from the deadline, and generates concise, non-nosy executive briefings.
"""

import os
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List

def call_groq_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Attempts to call Groq API if GROQ_API_KEY is configured.
    Falls back gracefully if not available.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or "your_" in api_key.lower():
        return ""
    
    try:
        import requests
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 1500
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=8)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        pass
    return ""

def synthesize_research(event_title: str, category: str, deadline: str, links: List[Dict[str, Any]], user_notes: str = "") -> Dict[str, Any]:
    """
    Combines scraped web content and extracts structured research,
    event tracks, deadlines, requirements, and targeted user questions.
    """
    combined_text = "\n\n".join([f"Link: {l.get('url')}\nTitle: {l.get('title')}\nSummary: {l.get('summary')}\nContent: {l.get('raw_text', '')[:1500]}" for l in links])
    if user_notes:
        combined_text += f"\n\nUser Notes: {user_notes}"
        
    # Attempt LLM synthesis
    llm_system = "You are CHRONOS, an expert autonomous hackathon architect. Analyze this event. Output pure JSON with keys: summary (string), key_deadlines (list of strings), requirements (list of strings), tracks_or_prizes (list of strings), recommended_stack (list of strings), clarification_questions (list of 3 precise questions asking the user what specific track, stack, and deliverables they want to build)."
    llm_user = f"Event Title: {event_title}\nCategory: {category}\nTarget Deadline: {deadline}\n\nScraped Data:\n{combined_text[:4000]}"
    
    llm_response = call_groq_llm(llm_system, llm_user)
    if llm_response:
        try:
            # Clean json fences
            clean_json = re.sub(r'```(?:json)?', '', llm_response).strip()
            data = json.loads(clean_json)
            if all(k in data for k in ["summary", "clarification_questions"]):
                return data
        except Exception:
            pass
            
    # Deterministic Heuristic Synthesis (Zero-Downtime Guarantee)
    summary = f"Autonomous analysis for '{event_title}'. Portal links parsed: {len(links)} external references ingested. Scraped materials highlight key submission checkpoints and functional criteria."
    
    # Extract deadlines found
    all_dates = []
    for l in links:
        all_dates.extend(l.get("dates_found", []))
    key_deadlines = list(dict.fromkeys(all_dates))[:4] or [f"Final Submission: {deadline}", "2-Hour Pre-Deadline Freeze", "Live Code Repository Lock"]
    
    requirements = [
        "Public or designated GitHub repository with structured commit history",
        "Clean architectural diagram & comprehensive README with quickstart",
        "Functional working demo video (2–3 minutes max, hosted on YouTube/Loom)",
        "Compliance with competition evaluation rubrics and API rules"
    ]
    
    tracks_or_prizes = [
        f"Main Track: Autonomous Systems & Agentic Solutions",
        f"API Innovation Bounty: Integration with ecosystem tools",
        f"Design & UX Excellence: Sleek, responsive interface"
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
        "summary": summary,
        "key_deadlines": key_deadlines,
        "requirements": requirements,
        "tracks_or_prizes": tracks_or_prizes,
        "recommended_stack": recommended_stack,
        "clarification_questions": clarification_questions
    }

def generate_phased_tasks(event_id: int, event_title: str, deadline_str: str, 
                          research_data: Dict[str, Any], user_focus: str = "") -> List[Dict[str, Any]]:
    """
    Calculates milestone intervals backwards from the deadline and decomposes
    the project into 4 structured phases with assigned MCP tools.
    """
    now = datetime.now()
    try:
        deadline_dt = datetime.fromisoformat(deadline_str.replace("Z", ""))
    except Exception:
        deadline_dt = now + timedelta(days=2)
        
    total_duration = max((deadline_dt - now).total_seconds(), 3600)
    
    # Backwards calculation intervals
    d_setup = (now + timedelta(seconds=total_duration * 0.15)).strftime("%Y-%m-%d %H:%M")
    d_core = (now + timedelta(seconds=total_duration * 0.50)).strftime("%Y-%m-%d %H:%M")
    d_polish = (now + timedelta(seconds=total_duration * 0.80)).strftime("%Y-%m-%d %H:%M")
    d_submit = (now + timedelta(seconds=total_duration * 0.95)).strftime("%Y-%m-%d %H:%M")
    
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
            "assigned_mcp": "SQLite MCP + Firecrawl MCP"
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
    """
    Produces a crisp, 1-2 sentence executive briefing that tells the user
    what to do next without being annoying or long-winded.
    """
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
    """
    Conversational agent handler with progressive disclosure.
    Guides the user through event intake, asks scoping questions,
    and progressively reveals tasks, MCP configurations, and calendar slots.
    """
    from sentinel.db import (
        get_events, create_event, add_event_link, update_event_link,
        save_event_research, get_event_research, create_task, get_tasks,
        save_mcp_config, get_mcp_configs
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
        page_title = scrape_res.get("title") or "Hackathon Event"
        
        # Clean title if long
        event_title = page_title.split("|")[0].split(" - ")[0].strip()[:60]
        if len(event_title) < 5 or "http" in event_title.lower():
            event_title = "Hackathon Submission Milestone"

        # Determine deadline from text or scraped dates
        dates_found = scrape_res.get("dates_found", [])
        now = datetime.now()
        target_deadline = (now + timedelta(days=2, hours=12)).isoformat()
        
        # Look for explicit deadline words in user text
        if "sunday" in user_text_clean.lower():
            days_ahead = (6 - now.weekday()) % 7 or 7
            target_deadline = (now + timedelta(days=days_ahead, hours=18)).isoformat()
        elif "tomorrow" in user_text_clean.lower():
            target_deadline = (now + timedelta(days=1, hours=18)).isoformat()

        # Create event
        event_id = create_event(
            title=event_title,
            category="hackathon",
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
            category="hackathon",
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

        # Conversational Progressive Response
        questions_formatted = "\n".join([f"- {q}" for q in research["clarification_questions"][:3]])
        formatted_date = target_deadline[:16].replace('T', ' ')
        content = (
            f"I have digested the links for **{event_title}**.\n\n"
            f"**Key Deadline Target:** `{formatted_date}`\n\n"
            f"Before I decompose your workflow and configure the MCPs, answer these 3 quick scoping questions so I don't give you generic tasks:\n\n"
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

    # 2. Check if user is specifying task scope / answering scoping questions
    events = get_events()
    recent_event = events[0] if events else None

    keywords_trigger = ["track", "python", "backend", "frontend", "solo", "team", "focus", "build", "agent", "mvp", "stack", "task", "yes", "no"]
    is_scoping_answer = recent_event and any(kw in user_text_clean.lower() for kw in keywords_trigger)

    if is_scoping_answer and recent_event:
        event_id = recent_event["id"]
        research = get_event_research(event_id) or {}
        
        # Generate Phased Tasks
        tasks = generate_phased_tasks(
            event_id=event_id,
            event_title=recent_event["title"],
            deadline_str=recent_event["deadline"],
            research_data=research,
            user_focus=user_text_clean
        )

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

        # Auto-resolve MCPs
        rec_mcps = recommend_mcps_for_event(tasks, [], user_text_clean)
        for m in rec_mcps:
            save_mcp_config(
                event_id=event_id,
                mcp_name=m["name"],
                description=m["description"],
                install_command=m["install_command"],
                config_json=m["config_json"]
            )

        content = (
            f"Got it. I've tailored your roadmap for **{recent_event['title']}** based on your inputs:\n\n"
            f"1. **Phased Milestones:** 4 chronological phases scheduled backwards from your deadline.\n"
            f"2. **MCP Suite Configured:** Auto-selected {len(rec_mcps)} relevant MCP tools (e.g., {', '.join([m['name'] for m in rec_mcps[:3]])}).\n"
            f"3. **Deadline Guard:** Executive reminder daemon is monitoring your due dates."
        )

        return {
            "role": "assistant",
            "content": content,
            "card_type": "tasks_and_mcps",
            "metadata": {
                "event_id": event_id,
                "event_title": recent_event["title"],
                "tasks": created_tasks,
                "mcps": rec_mcps
            }
        }

    # 3. Status or Deadline Query
    if any(q in user_text_clean.lower() for q in ["status", "deadline", "briefing", "schedule", "calendar", "what's next"]):
        if not recent_event:
            return {
                "role": "assistant",
                "content": "You have no active events tracked right now. Paste an event link or type your deadline to start.",
                "card_type": None,
                "metadata": {}
            }
        tasks = get_tasks(recent_event["id"])
        pending = [t for t in tasks if t["status"] != "done"]
        briefing = generate_non_nosy_briefing(recent_event, pending)
        return {
            "role": "assistant",
            "content": f"**[{briefing['header']}]**\n{briefing['message']}",
            "card_type": "briefing_card",
            "metadata": {
                "event_id": recent_event["id"],
                "briefing": briefing,
                "pending_tasks": pending[:3]
            }
        }

    # 4. WhatsApp / Social Media Connect Query
    if any(c in user_text_clean.lower() for c in ["whatsapp", "telegram", "discord", "slack", "notify", "social", "phone"]):
        return {
            "role": "assistant",
            "content": (
                "You can connect WhatsApp, Telegram, Discord, or Slack to receive short executive briefings on your phone.\n\n"
                "Click the **'Connect Channels'** button in the header or provide your phone number/webhook URL to configure it."
            ),
            "card_type": "channel_connect_trigger",
            "metadata": {}
        }

    # 5. Default General Assistance
    return {
        "role": "assistant",
        "content": (
            "I'm CHRONOS, your local deadline sentinel and MCP orchestrator.\n\n"
            "Paste your hackathon or project link, or tell me about an upcoming event with its deadline. "
            "I'll digest the links, ask what you need, configure the relevant MCPs, and keep you ahead of your milestones."
        ),
        "card_type": None,
        "metadata": {}
    }

