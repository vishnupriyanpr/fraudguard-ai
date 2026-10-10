"""
CHRONOS // Master Application Launcher
Boots up the local FastAPI Sentinel, initializes SQLite persistence,
seeds initial hackathon context if empty, and launches the browser UI.
"""

import sys
import os
import webbrowser
import threading
import time
from datetime import datetime, timedelta

# Ensure parent directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sentinel.db import init_db, get_events, create_event, save_event_research, create_task, save_mcp_config, create_reminder, add_event_link

def seed_sample_event_if_empty():
    """Seeds a realistic hackathon test event so the interface is immediately populated."""
    events = get_events()
    if len(events) == 0:
        print("[CHRONOS] First run detected. Seeding benchmark hackathon event...")
        now = datetime.now()
        target_deadline = (now + timedelta(hours=36, minutes=30)).isoformat()
        
        event_id = create_event(
            title="TigerGraph x HackerHouse Frontier Hackathon",
            category="hackathon",
            deadline=target_deadline,
            description="Agentic graph investigation system challenge for fraud detection and financial intelligence.",
            user_notes="Prioritizing autonomous multi-hop topology traversal, sub-second Groq inference, and automated SAR filings."
        )
        
        # Add links
        add_event_link(event_id, "https://devpost.com/software/fraudguard-ai", "FraudGuard Submission Portal")
        add_event_link(event_id, "https://docs.tigergraph.com/tigergraph-server/current/intro/", "TigerGraph Server Docs")
        
        # Save research dossier
        save_event_research(
            event_id=event_id,
            summary="Autonomous graph agentic challenge requiring IEEE-CIS dataset evaluation, GSQL topological schema integration, and regulatory SAR generation under strict time constraints.",
            key_deadlines=[
                f"Portal Submissions Close: {target_deadline}",
                "Final Code Repository Lock: 2 hours prior",
                "Video Demo Upload Limit: 3 minutes max"
            ],
            requirements=[
                "GitHub repository with clean commit progression and MIT license",
                "Working demo video uploaded to YouTube or Loom",
                "GSQL graph queries exported and verified in TGCloud 4.2",
                "Documentation meeting all 36 evaluation criteria"
            ],
            tracks_or_prizes=[
                "Grand Prize: Best Autonomous Agentic System ($10,000)",
                "TigerGraph GraphRAG Bounty: Topological Knowledge Extraction",
                "FinTech Excellence: Next Best Action Policy Engine"
            ],
            recommended_stack=[
                "Backend: Python FastAPI + pyTigerGraph",
                "Inference: Groq LPU Frontier Models (Llama 3.3 / Qwen)",
                "MCP Tools: GitHub MCP, TigerGraph MCP, Chrome DevTools MCP"
            ],
            clarification_questions=[
                "1. Which prize track are you prioritizing: Grand Prize Autonomous Agent or GraphRAG Bounty?",
                "2. Have you verified your TigerGraph Cloud 4.2 connection secret and auth token?",
                "3. Do you have your 2-minute demo video script prepared?"
            ]
        )
        
        # Phased Tasks
        t1 = (now + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M")
        t2 = (now + timedelta(hours=16)).strftime("%Y-%m-%d %H:%M")
        t3 = (now + timedelta(hours=28)).strftime("%Y-%m-%d %H:%M")
        t4 = (now + timedelta(hours=34)).strftime("%Y-%m-%d %H:%M")
        
        create_task(event_id, "Phase 1: Environment Setup & TigerGraph Cloud Schema Ingestion", "Set up pyTigerGraph client, configure TG_HOST, TG_USERNAME and verify GSQL connectivity.", "Phase 1: Setup", t1, "high", "Filesystem MCP + TigerGraph MCP")
        create_task(event_id, "Phase 2: Core Autonomous Investigation Pipeline & EVOI Logic", "Build Shannon entropy calculator, dual-state NBA router, and Groq SAR filing engine.", "Phase 2: MVP Core", t2, "high", "SQLite MCP + GitHub MCP")
        create_task(event_id, "Phase 3: Monochrome Dashboard & Edge-Case Benchmark Suite", "Verify all 20 test cases pass strict validation with zero false negatives.", "Phase 3: Polish & UI", t3, "medium", "Chrome DevTools MCP")
        create_task(event_id, "Phase 4: Record 2-Min Demo Video, Finalize README & Submit Portal", "Publish video walkthrough, lock GitHub release tag, and submit to portal.", "Phase 4: Submission", t4, "high", "GitHub MCP + Slack MCP")
        
        # MCP Configs
        save_mcp_config(
            event_id, "TigerGraph MCP", 
            "Native graph database connection, GSQL query execution, and topological graph traversal.",
            "uvx tigergraph-mcp",
            {"command": "uvx", "args": ["tigergraph-mcp"], "env": {"TG_HOST": "<TG_HOST>", "TG_USERNAME": "<TG_USERNAME>"}}
        )
        save_mcp_config(
            event_id, "GitHub MCP", 
            "Automates repository branching, commits, pull requests, and submission tagging.",
            "npx -y @modelcontextprotocol/server-github",
            {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"], "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "<TOKEN>"}}
        )
        save_mcp_config(
            event_id, "Chrome DevTools MCP", 
            "Headless browser control, UI element inspection, automated responsiveness checks.",
            "npx -y chrome-devtools-mcp",
            {"command": "npx", "args": ["-y", "chrome-devtools-mcp"], "env": {}}
        )
        
        # Initial briefing
        create_reminder(
            event_id,
            f"[{round(36.5, 1)} hours remaining (TigerGraph Hackathon)] Current focus: 'Phase 1: Environment Setup & TigerGraph Cloud Schema Ingestion'. Step ahead of the curve.",
            "info"
        )
        print("[CHRONOS] Benchmark event seeded.")

def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    init_db()
    seed_sample_event_if_empty()
    
    import uvicorn
    from sentinel.main import app
    
    print("\n" + "="*70)
    print("  CHRONOS // AUTONOMOUS DEADLINE SENTINEL & MCP ORCHESTRATOR")
    print("  Local UI:  http://127.0.0.1:8000")
    print("  Palette:   Pure Black (#000000), Pure White (#FFFFFF), Grey (#71717A)")
    print("="*70 + "\n")
    
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
