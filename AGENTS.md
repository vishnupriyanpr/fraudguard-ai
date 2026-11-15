# Agent Guidelines: CHRONOS // Autonomous Deadline Sentinel

## Package Manager & Runtime
- **Python**: 3.10+ with `pip` / `uv`
- **Install**: `pip install -r requirements.txt`
- **Run Server**: `python run_sentinel.py` (Default: `http://127.0.0.1:8000`)

## File-Scoped Commands
| Task | Command |
|------|---------|
| Unit & Integration Tests | `python -m pytest tests/test_chronos.py -v` |
| Fast Single Test | `python -m pytest tests/test_chronos.py -k test_calendar_export_ics -v` |
| Database Integrity Check | `python -c "import sqlite3; conn = sqlite3.connect('chronos.db'); print(conn.execute('PRAGMA integrity_check').fetchall())"` |
| Calendar ICS Export Test | `python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/api/calendar/export.ics').status)"` |

## Commit Attribution
AI commits MUST include:
```
Co-authored-by: Vivek K K <189313098+Vivek-the-creator@users.noreply.github.com>
```

## Core Architecture & Conventions
- **Zero Mock Policy**: All features, buttons, and API endpoints must execute real logic.
- **RESTful API Boundaries**:
  - `GET /api/briefing`: Non-nosy countdown and immediate priority milestone.
  - `GET /api/events`: Event registry ordered by deadline or recency.
  - `POST /api/chat`: Autonomous planning and model thinking turn.
  - `GET /api/calendar/export.ics`: RFC 5545 iCalendar stream with tiered `-PT24H`, `-PT2H`, `-PT30M` alarms.
  - `POST /api/integrations/google-calendar/sync`: Real 1-click Google Calendar web intent URL.
  - `GET /api/database/verify`: Real SQLite `PRAGMA integrity_check`.
- **Design System**: Linear/Shadcn monochromatic zinc aesthetic (`#09090b`, `#71717a`, `#e4e4e7`, `#ffffff`).
- **Timezone Safety**: All datetime operations must be offset-aware UTC (`timezone.utc`).
- **Model Intelligence**: Reason dynamically across Conferences, Hackathons, Grants, and Projects. Never output hardcoded templates.
