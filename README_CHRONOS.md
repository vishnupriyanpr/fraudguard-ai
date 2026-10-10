# CHRONOS // Autonomous Event Deadline Sentinel & MCP Orchestrator

> **Local autonomous companion that ingests event and hackathon links, extracts submission criteria, asks clarifying scoping questions, decomposes phased milestones backwards from deadlines, auto-resolves Model Context Protocol (MCP) tooling, and delivers low-noise executive briefings via Chat, WhatsApp, Telegram, Discord, and Slack.**

---

## System Capabilities

### 1. Autonomous Link Scraper & Deep Pre-Research
- Ingests event portal links (Devpost, Taikai, GitHub repositories, documentation pages).
- Autonomous DOM parser extracts closing dates, evaluation rubrics, prize tracks, and tech criteria.
- Compiles an executive pre-research dossier before you start building.

### 2. Conversational Scoping & Progressive Disclosure
- Designed as a chat agent that converses with you rather than dumping raw data all at once.
- Formulates 3 targeted scoping questions based on the event:
  - Targeted prize tracks or bounties
  - Solo vs. team architectural requirements
  - Environment credentials vs. automated mock pipelines
- As you clarify your focus, it dynamically decomposes your workflow into 4 phased checkpoints.

### 3. Backwards-Scheduled Milestone Matrix
- Calculates milestone intervals backwards from the deadline:
  - **Phase 1: Setup & Environment**: Repository scaffolding and API keys.
  - **Phase 2: MVP Core Architecture**: Primary business logic and engine.
  - **Phase 3: Polish & UI Testing**: Minimalist interface, error boundaries, smoke tests.
  - **Phase 4: Submission Buffer**: 2-minute demo video, documentation, and submission portal lock.

### 4. Autonomous MCP Resolution & Auto-Configuration
- Analyzes project tasks to auto-resolve and configure required Model Context Protocol servers:
  - **GitHub MCP**: Branching, commits, pull requests, release tagging.
  - **Firecrawl MCP**: Autonomous documentation scraping.
  - **Chrome DevTools MCP**: Automated UI testing and screenshot artifacts.
  - **SQLite MCP**: Relational state persistence.
  - **TigerGraph MCP**: Graph database queries.
  - **Filesystem MCP**: Codebase scaffolding and file generation.
- 1-click configuration export directly to `mcp_servers.json` for Claude Desktop, Cursor, and Antigravity.

### 5. Multi-Platform Messaging Integration
- Direct connectors for low-noise executive briefings:
  - **WhatsApp**: Direct phone alerts via Webhook Gateway / Local Bridge.
  - **Telegram**: Private bot alerts with Chat ID routing.
  - **Discord**: Webhook alerts to dedicated channels.
  - **Slack**: Webhook alerts to development channels.
- Rate-limited background daemon ensures zero spam: at most one 1-2 sentence briefing every few hours, tightening only in the final hours before submission.

### 6. Editorial Minimalist Interface
- **Pure Monochrome**: Clean editorial white canvas (`#FFFFFF`), light grey surfaces, crisp 1px borders (`#E5E5E8`), and dark typography.
- **Typography**: Powered by Satoshi font paired with JetBrains Mono.
- **Pure Vector SVGs**: Zero emojis across the entire UI and codebase.

---

## Quickstart

### Prerequisites
- Python 3.10+
- Node.js & npm (for MCP execution)

### 1. Installation
```bash
git clone https://github.com/vishnupriyanpr/CHRONOS.git
cd CHRONOS
pip install -r requirements.txt
```

### 2. Start Local Sentinel
```bash
python run_sentinel.py
```
The application will launch on **http://127.0.0.1:8000** and automatically open in your default browser.

### 3. Run Automated Tests
```bash
python -m pytest tests/test_chronos.py -v
```

---

## Architecture

```
CHRONOS/
├── run_sentinel.py           # Entrypoint launcher & browser auto-opener
├── mcp_servers.json          # Exported MCP servers configuration
├── chronos.db                # SQLite persistence (events, tasks, channels, chat)
├── sentinel/
│   ├── main.py               # FastAPI application & REST/Chat API
│   ├── db.py                 # SQLite schema & data access layer
│   ├── scraper.py            # Autonomous link crawler & HTML extractor
│   ├── ai_engine.py          # Chatbot logic, scoping agent & task generator
│   ├── mcp_manager.py        # MCP catalog & config exporter
│   ├── reminder_service.py   # Background daemon for deadline monitoring
│   ├── channel_service.py    # WhatsApp, Telegram, Discord, Slack dispatcher
│   └── static/
│       ├── index.html        # Minimalist white-themed chatbot interface
│       ├── style.css         # Satoshi typography & responsive styles
│       └── app.js            # Progressive disclosure & client state
└── tests/
    └── test_chronos.py       # End-to-end automated test suite
```

---

## License
MIT License
