"""
Case Memory System for FraudGuard AI.
Stores and retrieves historical closed cases and newly closed investigation records.
"""

from typing import List, Dict, Any, Optional
import json
import os


class CaseMemoryManager:
    """Manages case memory across historical and live investigations."""

    def __init__(self, graph_engine):
        self.graph_engine = graph_engine
        self.live_cases: Dict[str, Dict[str, Any]] = {}

    def retrieve_similar_cases(
        self,
        pattern: str,
        customer_id: str,
        card_id: str,
        device_profile: str,
        as_of_ts: str,
        top_k: int = 3
    ) -> List[str]:
        """
        Retrieve case IDs of the most relevant prior investigations.
        Returns list of case IDs, e.g. ['CC-0141', 'CC-2671']
        """
        # 1. Search historical closed cases
        historical_matches = self.graph_engine.find_similar_closed_cases(
            pattern=pattern,
            customer_id=customer_id,
            card_id=card_id,
            device_profile=device_profile,
            as_of_ts=as_of_ts,
            top_k=top_k
        )

        case_ids = [m["case_id"] for m in historical_matches if "case_id" in m]

        # 2. Check live memory from current run
        for cid, case_data in self.live_cases.items():
            if len(case_ids) >= top_k:
                break
            if case_data.get("closed_at", "") <= as_of_ts:
                if case_data.get("customer_id") == customer_id or case_data.get("pattern") == pattern:
                    if cid not in case_ids:
                        case_ids.append(cid)

        return case_ids[:top_k]

    def record_investigation(self, case_id: str, case_data: Dict[str, Any]):
        """Save completed case into live case memory."""
        self.live_cases[case_id] = case_data
