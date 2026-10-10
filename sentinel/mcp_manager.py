"""
CHRONOS // Autonomous MCP Resolution & Config Generator
Detects required Model Context Protocol (MCP) servers based on tasks and research,
and generates auto-installation scripts and desktop configuration files.
"""

import os
import json
import subprocess
from typing import List, Dict, Any

MCP_CATALOG = {
    "github": {
        "name": "GitHub MCP",
        "description": "Automates repository branching, commits, pull requests, issue tracking, and submission diff checks.",
        "keywords": ["github", "git", "commit", "repo", "repository", "pr", "pull request", "branch"],
        "package": "@modelcontextprotocol/server-github",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env_required": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
        "recommended_for": "Code tracking, submission tagging, and team collaboration"
    },
    "firecrawl": {
        "name": "Firecrawl MCP",
        "description": "Autonomous deep-web scraping and Markdown extraction for competitor research and portal scraping.",
        "keywords": ["scrape", "crawl", "web", "research", "portal", "link", "documentation", "rules"],
        "package": "firecrawl-mcp",
        "command": "npx",
        "args": ["-y", "firecrawl-mcp"],
        "env_required": ["FIRECRAWL_API_KEY"],
        "recommended_for": "Autonomous document extraction and competitor benchmarking"
    },
    "chrome-devtools": {
        "name": "Chrome DevTools MCP",
        "description": "Headless browser control, UI element inspection, automated responsiveness checks, and demo screenshots.",
        "keywords": ["ui", "frontend", "browser", "inspect", "screenshot", "demo", "testing", "e2e"],
        "package": "chrome-devtools-mcp",
        "command": "npx",
        "args": ["-y", "chrome-devtools-mcp"],
        "env_required": [],
        "recommended_for": "Automated UI quality assurance and presentation artifact generation"
    },
    "sqlite": {
        "name": "SQLite MCP",
        "description": "Local zero-overhead relational database inspection, table querying, and state persistence.",
        "keywords": ["database", "sqlite", "sql", "data", "tables", "persistence", "queries"],
        "package": "mcp-server-sqlite",
        "command": "uvx",
        "args": ["mcp-server-sqlite", "--db-path", "chronos.db"],
        "env_required": [],
        "recommended_for": "Instant local data modeling and state verification"
    },
    "tigergraph": {
        "name": "TigerGraph MCP",
        "description": "Native graph database connection, GSQL query execution, and topological graph traversal.",
        "keywords": ["tigergraph", "gsql", "graph", "knowledge graph", "fraudguard", "vertices", "edges"],
        "package": "tigergraph-mcp",
        "command": "uvx",
        "args": ["tigergraph-mcp"],
        "env_required": ["TG_HOST", "TG_USERNAME", "TG_PASSWORD"],
        "recommended_for": "Complex entity-relationship mapping and high-scale graph computing"
    },
    "filesystem": {
        "name": "Filesystem MCP",
        "description": "Secure local directory read/write access for codebase scaffolding and artifact management.",
        "keywords": ["files", "filesystem", "project", "scaffold", "directory", "local", "code"],
        "package": "@modelcontextprotocol/server-filesystem",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
        "env_required": [],
        "recommended_for": "Autonomous file creation and project artifact organization"
    },
    "slack": {
        "name": "Slack MCP",
        "description": "Real-time dispatch of deadline alerts and build status updates to project channels.",
        "keywords": ["slack", "notification", "team", "alert", "channel", "message"],
        "package": "@modelcontextprotocol/server-slack",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-slack"],
        "env_required": ["SLACK_BOT_TOKEN"],
        "recommended_for": "Team deadline broadcast without intrusive manual pings"
    }
}

def recommend_mcps_for_event(tasks: List[Dict[str, Any]], keywords: List[str], text_corpus: str) -> List[Dict[str, Any]]:
    """
    Intelligently scores and recommends the top MCPs needed for this specific event and task set.
    """
    recommended = []
    text_lower = (text_corpus + " " + " ".join(keywords) + " " + " ".join([t.get("title", "") + " " + t.get("description", "") for t in tasks])).lower()
    
    # Always include filesystem and github as foundational dev MCPs
    scores = {mcp_id: 1.0 if mcp_id in ["filesystem", "github"] else 0.0 for mcp_id in MCP_CATALOG}
    
    for mcp_id, data in MCP_CATALOG.items():
        for kw in data["keywords"]:
            if kw in text_lower:
                scores[mcp_id] += 1.5
                
    # Rank by score
    sorted_mcps = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    for mcp_id, score in sorted_mcps:
        if score >= 1.0:
            item = MCP_CATALOG[mcp_id].copy()
            item["id"] = mcp_id
            item["score"] = score
            item["install_command"] = f"{item['command']} {' '.join(item['args'])}"
            item["config_json"] = {
                "command": item["command"],
                "args": item["args"],
                "env": {k: f"<{k}_VALUE>" for k in item["env_required"]}
            }
            recommended.append(item)
            
    return recommended

def generate_unified_config(selected_mcps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates standard Claude Desktop / Cursor / Antigravity MCP config JSON.
    """
    mcp_servers = {}
    for mcp in selected_mcps:
        mcp_servers[mcp["id"]] = {
            "command": mcp.get("command", "npx"),
            "args": mcp.get("args", []),
            "env": {k: os.getenv(k, f"<{k}_VALUE>") for k in mcp.get("env_required", [])}
        }
    return {"mcpServers": mcp_servers}

def save_mcp_config_to_disk(config_dict: Dict[str, Any], filepath: str = "mcp_servers.json") -> str:
    """
    Writes configuration to local root for immediate agent / IDE binding.
    """
    full_path = os.path.abspath(filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2)
    return full_path
