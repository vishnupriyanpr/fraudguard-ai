"""
Autonomous Exam Period Real-Time Monitor for FraudGuard AI.
Monitors November & December 2016 transactions, identifies emerging risk score surges,
runs end-to-end agentic investigations, and persists case packages to cases_innovative/.
Directly addresses the Hackathon Innovation Challenge.
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Any
import polars as pl
import pandas as pd

from src.agent.graph_engine import GraphInvestigationEngine
from src.agent.investigator import FraudInvestigationAgent


class ExamPeriodFraudMonitor:
    """
    Continuous streaming-style alert detector and autonomous investigator.
    Scans the exam window (November-December 2016) for real-time model alerts.
    """

    def __init__(self, data_dir: str = "data", output_dir: str = "cases_innovative"):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.tx_path = os.path.join(data_dir, "transactions.csv")
        self.engine = GraphInvestigationEngine(data_dir=data_dir)
        self.agent = FraudInvestigationAgent(graph_engine=self.engine)
        os.makedirs(output_dir, exist_ok=True)

    def scan_for_alerts(
        self,
        min_risk_score: float = 0.88,
        min_amount: float = 50.0,
        start_date: str = "2016-11-01",
        end_date: str = "2016-12-31",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Scan transactions during the exam period for high-risk anomalies.
        Excludes transactions already covered in the official 20 case_pack.
        """
        pack_path = os.path.join(self.data_dir, "case_pack.csv")
        excluded_txns = set()
        if os.path.exists(pack_path):
            df_pack = pd.read_csv(pack_path)
            excluded_txns = set(int(x) for x in df_pack["flagged_txn_id"].dropna().unique())

        q = pl.scan_csv(self.tx_path)
        candidates = q.filter(
            (pl.col("ts") >= start_date) &
            (pl.col("ts") <= end_date) &
            (pl.col("risk_score") >= min_risk_score) &
            (pl.col("TransactionAmt") >= min_amount)
        ).collect().to_dicts()

        # Filter out existing benchmark cases and pick diverse candidates
        unique_alerts = []
        seen_customers = set()

        for c in candidates:
            tid = int(c["TransactionID"])
            cid = c.get("customer_id")
            if tid in excluded_txns or cid in seen_customers:
                continue
            seen_customers.add(cid)
            unique_alerts.append(c)
            if len(unique_alerts) >= limit:
                break

        return unique_alerts

    def monitor_and_investigate(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Scan, investigate, and produce innovative case files.
        """
        print(f"Scanning exam period (Nov-Dec 2016) for emerging high-risk alerts...")
        raw_alerts = self.scan_for_alerts(limit=limit)
        print(f"Found {len(raw_alerts)} candidate alerts across distinct accounts.\n")

        results = []
        for i, alert in enumerate(raw_alerts):
            case_id = f"INV-{i+1:03d}"
            tid = int(alert["TransactionID"])
            cid = alert["customer_id"]
            ts = alert["ts"]
            amt = float(alert.get("TransactionAmt", 0.0))
            score = float(alert.get("risk_score", 0.0))
            channel = alert.get("channel", "online")

            case_row = {
                "case_id": case_id,
                "opened_at": ts,
                "trigger_type": "risk_score",
                "trigger_text": f"Continuous monitor alert: Model scored transaction {tid} (${amt:.2f}, {channel}) at {score:.2f} during exam period.",
                "flagged_txn_id": tid,
                "card_id": f"{cid}-K1",
                "customer_id": cid,
                "risk_score": score
            }

            sub = self.agent.investigate_case(case_row)
            sub_dict = sub.model_dump()
            results.append(sub_dict)

            out_path = os.path.join(self.output_dir, f"{case_id}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(sub_dict, f, indent=2)

            print(f"[{case_id}] Txn {tid} (${amt:.2f}) -> Verdict: {sub.case.verdict.upper()} | Pattern: {sub.case.pattern} | SAR: {sub.sar.file}")

        # Summary file for innovation deliverables
        summary = {
            "monitored_period": "2016-11-01 to 2016-12-31",
            "total_autonomous_alerts_resolved": len(results),
            "output_directory": self.output_dir,
            "generated_at": datetime.now().isoformat()
        }
        with open(os.path.join(self.output_dir, "innovation_summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        print(f"\nSaved {len(results)} innovative case investigations into '{self.output_dir}/'.")
        return results
