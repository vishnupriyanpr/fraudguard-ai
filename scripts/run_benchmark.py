import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
"""
Benchmark Execution Runner for FraudGuard AI.
Runs the autonomous agent on all 20 cases from case_pack.csv,
generates valid submission files in cases/ and output/benchmark_cases/,
and produces a summary telemetry report.
"""

import os
import sys
import json
import time
import pandas as pd

from src.agent.graph_engine import GraphInvestigationEngine
from src.agent.investigator import FraudInvestigationAgent


def run_all_benchmarks():
    print("=================================================================")
    print("  ??? FraudGuard AI ? Running 20 Benchmark Investigations (HHGoa)  ")
    print("=================================================================\n")

    start_total = time.time()
    data_dir = "data"
    pack_path = os.path.join(data_dir, "case_pack.csv")
    if not os.path.exists(pack_path):
        print(f"Error: {pack_path} not found!")
        return

    cases_dir = "cases"
    output_dir = os.path.join("output", "benchmark_cases")
    os.makedirs(cases_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    print("Step 1: Initializing TigerGraph / Graph Engine...")
    t0 = time.time()
    engine = GraphInvestigationEngine(data_dir=data_dir)
    print(f"Graph Engine ready in {time.time() - t0:.2f}s.\n")

    print("Step 2: Launching Fraud Investigation Agent...")
    agent = FraudInvestigationAgent(graph_engine=engine)
    df_pack = pd.read_csv(pack_path)

    results = []
    fraud_count = 0
    legit_count = 0
    uncertain_count = 0
    sar_count = 0
    total_exposure = 0.0

    print("Step 3: Investigating Benchmark Cases...\n")
    for idx, row in df_pack.iterrows():
        case_id = row["case_id"]
        t_case = time.time()
        sub = agent.investigate_case(row.to_dict())
        latency = round(time.time() - t_case, 2)
        sub.latency_s = latency

        sub_dict = sub.model_dump()
        results.append(sub_dict)

        # Write to cases/<case_id>.json (primary submission requirement)
        case_path_primary = os.path.join(cases_dir, f"{case_id}.json")
        with open(case_path_primary, "w", encoding="utf-8") as f:
            json.dump(sub_dict, f, indent=2)

        # Mirror to output/benchmark_cases/<case_id>.json
        case_path_mirror = os.path.join(output_dir, f"{case_id}.json")
        with open(case_path_mirror, "w", encoding="utf-8") as f:
            json.dump(sub_dict, f, indent=2)

        # Stats
        verdict = sub.case.verdict
        pattern = sub.case.pattern
        exp = sub.case.exposure_usd
        sar = sub.sar.file

        if verdict == "fraud":
            fraud_count += 1
            total_exposure += exp
        elif verdict == "legitimate":
            legit_count += 1
        else:
            uncertain_count += 1

        if sar:
            sar_count += 1

        print(f"[{idx+1:02d}/20] {case_id} -> Verdict: {verdict.upper():<10} | Pattern: {pattern:<25} | Exposure: ${exp:>8.2f} | SAR: {'YES' if sar else 'NO':<3} | Time: {latency:.2f}s")

    summary = {
        "benchmark_run_at": datetime.now().isoformat() if "datetime" in globals() else time.ctime(),
        "total_cases_investigated": len(results),
        "verdict_distribution": {
            "fraud": fraud_count,
            "legitimate": legit_count,
            "uncertain": uncertain_count
        },
        "regulatory_sars_filed": sar_count,
        "total_fraud_exposure_identified_usd": round(total_exposure, 2),
        "total_run_latency_s": round(time.time() - start_total, 2),
        "average_latency_per_case_s": round((time.time() - start_total) / len(results), 2)
    }

    summary_path = os.path.join(output_dir, "benchmark_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n=================================================================")
    print("  ?? BENCHMARK INVESTIGATION SUMMARY REPORT")
    print("=================================================================")
    print(f"Total Cases Investigated: {len(results)}")
    print(f"  ? Confirmed Fraud:     {fraud_count}")
    print(f"  ? Cleared Legitimate:  {legit_count}")
    print(f"  ? Escalated/Uncertain: {uncertain_count}")
    print(f"Regulatory SARs Filed:   {sar_count}")
    print(f"Total Fraud Exposure:    ${total_exposure:,.2f} USD")
    print(f"Total Execution Time:    {time.time() - start_total:.2f}s")
    print(f"Answer files generated:  '{cases_dir}/' ({len(results)} JSON files)")
    print("=================================================================\n")


if __name__ == "__main__":
    from datetime import datetime
    run_all_benchmarks()
