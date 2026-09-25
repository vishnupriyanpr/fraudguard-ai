"""
Groq LLM Client for FraudGuard AI.
Integrates high-speed frontier models on Groq:
- openai/gpt-oss-120b (Deep Reasoning, Complex Graph Explanation)
- qwen/qwen3.8-27b (Ultra-fast real-time inference & FinCEN SAR narrative synthesis)

Includes automatic model fallback and sanitization for Windows environments.
"""

from __future__ import annotations
import os
import re
import time
from typing import Dict, Any, List, Optional
import requests


def _load_local_env():
    """Load .env file if present in workspace root."""
    try:
        env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
        if os.path.exists(env_file):
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
    except Exception:
        pass

_load_local_env()


class GroqLLMClient:
    """
    High-performance LLM client powered by Groq LPUs.
    """

    PRIMARY_MODEL = "qwen/qwen3.8-27b"
    REASONING_MODEL = "openai/gpt-oss-120b"
    API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        self.enabled = bool(self.api_key and self.api_key.startswith("gsk_"))
        self.total_tokens_used = 0

    def _sanitize(self, text: str) -> str:
        """Replace non-standard unicode characters that can break Windows encodings."""
        if not text:
            return ""
        text = text.replace("\u202f", " ").replace("\u2011", "-").replace("\u2018", "'").replace("\u2019", "'")
        text = text.replace("\u201c", '"').replace("\u201d", '"').replace("\u2013", "-").replace("\u2014", "-")
        return text

    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: int = 250,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Invoke Groq chat completion API with latency and token usage tracking.
        """
        if not self.enabled:
            return {"content": "", "tokens": 0, "latency_s": 0.0, "status": "disabled"}

        selected_model = model or self.PRIMARY_MODEL
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "FraudGuard-AI/1.0",
        }
        payload = {
            "model": selected_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        start_time = time.perf_counter()
        try:
            resp = requests.post(self.API_URL, headers=headers, json=payload, timeout=25.0)
            latency = round(time.perf_counter() - start_time, 3)

            if resp.status_code == 200:
                data = resp.json()
                content = self._sanitize(data["choices"][0]["message"].get("content", "").strip())
                usage = data.get("usage", {})
                tokens = usage.get("total_tokens", int(max_tokens * 0.75))
                self.total_tokens_used += tokens
                return {
                    "content": content,
                    "tokens": tokens,
                    "latency_s": latency,
                    "model": selected_model,
                    "status": "success",
                }
            else:
                return {
                    "content": "",
                    "tokens": 0,
                    "latency_s": latency,
                    "error": resp.text,
                    "status": "error",
                }
        except Exception as e:
            latency = round(time.perf_counter() - start_time, 3)
            return {
                "content": "",
                "tokens": 0,
                "latency_s": latency,
                "error": str(e),
                "status": "exception",
            }

    def synthesize_sar_narrative(
        self,
        case_id: str,
        customer_id: str,
        card_id: str,
        flagged_txn_id: str,
        amount: float,
        exposure: float,
        channel: str,
        pattern: str,
        pattern_desc: str,
        opened_at: str,
        evidence_summary: str,
    ) -> Dict[str, Any]:
        """
        Draft a formal FinCEN 31 CFR 1020.320 SAR narrative using Groq LPU inference.
        """
        prompt = (
            f"Draft a formal 1-paragraph FinCEN Suspicious Activity Report (SAR) narrative in accordance with "
            f"31 CFR 1020.320 for Case {case_id}.\n"
            f"Subject: Customer {customer_id}, Card {card_id}.\n"
            f"Transaction {flagged_txn_id} (${amount:.2f}, {channel}) detected on {opened_at}.\n"
            f"Pattern: {pattern} ({pattern_desc}). Total unauthorized exposure: ${exposure:.2f}.\n"
            f"Key evidence: {evidence_summary}.\n"
            f"Explain why this activity is suspicious, how it violates policy, and state that the card has been blocked and retained for law enforcement."
        )

        messages = [
            {"role": "system", "content": "You are a senior AML compliance officer drafting FinCEN SAR narratives. Be objective, concise, and formal."},
            {"role": "user", "content": prompt},
        ]

        result = self.generate_chat_completion(
            messages=messages,
            model=self.PRIMARY_MODEL,
            max_tokens=220,
            temperature=0.1,
        )
        return result
