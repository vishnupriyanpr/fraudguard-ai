"""
CHRONOS // Autonomous Web Scraper & Link Intelligence Engine
Scrapes event links, extracts structured deadlines, tracks, requirements, and submission rules.
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from datetime import datetime

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def scrape_event_url(url: str, timeout: int = 8) -> Dict[str, Any]:
    """
    Fetches the URL, strips noisy markup, extracts key deadlines,
    rules, tracks, and returns a clean structured dossier.
    """
    result = {
        "url": url,
        "title": "",
        "summary": "",
        "raw_text": "",
        "dates_found": [],
        "keywords": [],
        "success": False,
        "error": None
    }
    
    try:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        html = resp.text
        
        soup = BeautifulSoup(html, "html.parser")
        
        # 1. Extract title
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.find("meta", property="og:title"):
            title = soup.find("meta", property="og:title").get("content", "").strip()
        elif soup.find("h1"):
            title = soup.find("h1").get_text().strip()
        result["title"] = title or url
        
        # 2. Extract description / summary
        desc = ""
        meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
        if meta_desc and meta_desc.get("content"):
            desc = meta_desc.get("content").strip()
            
        # 3. Strip script, style, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "noscript", "svg", "header"]):
            tag.decompose()
            
        text = soup.get_text(separator="\n")
        # Clean lines
        lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 2]
        clean_text = "\n".join(lines)
        
        # Limit text for token efficiency
        result["raw_text"] = clean_text[:12000]
        
        # Extract date-like patterns & deadlines
        date_patterns = [
            r'(?:deadline|due date|submission closes|ends on|timeline|starts on)[:\s]+([^\n\r\.\<\>]{5,60})',
            r'([A-Za-z]+ \d{1,2},? \d{4}(?: at \d{1,2}:\d{2}\s*(?:AM|PM|UTC|GMT|EST|PST))?)',
            r'(\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2})?)'
        ]
        
        dates_found = []
        for pat in date_patterns:
            matches = re.findall(pat, clean_text, flags=re.IGNORECASE)
            for m in matches:
                clean_m = m.strip() if isinstance(m, str) else m[0].strip()
                if len(clean_m) > 3 and clean_m not in dates_found:
                    dates_found.append(clean_m)
                    
        result["dates_found"] = dates_found[:8]
        
        # Detect event keywords
        keywords = []
        kw_list = [
            "Devpost", "Hackathon", "GitHub", "API", "Frontend", "Backend", 
            "Docker", "Database", "Demo Video", "TigerGraph", "Groq", "OpenAI", 
            "Solana", "Ethereum", "Prizes", "Rubric", "Evaluation", "Bounty"
        ]
        for kw in kw_list:
            if re.search(r'\b' + re.escape(kw) + r'\b', clean_text, re.IGNORECASE):
                keywords.append(kw)
        result["keywords"] = keywords
        
        # Create summary
        if desc:
            result["summary"] = desc
        else:
            first_chunk = " ".join(lines[:6])
            result["summary"] = first_chunk[:300] + ("..." if len(first_chunk) > 300 else "")
            
        result["success"] = True
        
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        result["title"] = url
        result["summary"] = f"Could not fetch link live ({str(e)}). Event intelligence will proceed using user context."
        
    return result
