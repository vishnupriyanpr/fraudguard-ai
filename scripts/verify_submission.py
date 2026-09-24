"""
Validation script for HHGoa Fraud Investigation Challenge.
Validates all 20 case files in cases/ against the exact JSON schema,
policy rules, and field requirements specified in README.md.
"""

import os
import json
import sys

def verify_all_cases(cases_dir="cases"):
    required_top_keys = {
        "case_id", "case", "evidence_requests", "next_best_actions",
        "sar", "stop_reason", "tool_calls", "tokens", "latency_s"
    }
    required_case_keys = {
        "status", "verdict", "fraud_probability", "pattern", "pattern_description",
        "affected_txn_ids", "first_suspicious_txn_id", "connected_card_ids",
        "connected_device_profiles", "exposure_usd", "evidence", "similar_prior_cases",
        "summary", "written_to_graph", "graph_case_id"
    }
    required_nba_keys = {"initial", "final", "what_changed"}
    required_sar_keys = {"file", "reason", "narrative", "subjects", "total_amount_usd", "activity_dates"}

    valid_patterns = {
        "card_testing", "card_not_present_fraud", "card_not_present_new_device",
        "out_of_region_use", "account_takeover", "undocumented", "none"
    }
    valid_statuses = {"open", "closed_fraud", "closed_legitimate", "escalated"}
    valid_verdicts = {"fraud", "legitimate", "uncertain"}

    errors = []

    if not os.path.exists(cases_dir):
        print(f"Error: Directory '{cases_dir}' not found.")
        sys.exit(1)

    files = [f for f in os.listdir(cases_dir) if f.endswith(".json")]
    if len(files) != 20:
        errors.append(f"Expected 20 files in {cases_dir}/, found {len(files)}")

    for f_name in sorted(files):
        path = os.path.join(cases_dir, f_name)
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                errors.append(f"{f_name}: Invalid JSON: {e}")
                continue

        for k in required_top_keys:
            if k not in data:
                errors.append(f"{f_name}: Missing top-level key '{k}'")

        case = data.get("case", {})
        for k in required_case_keys:
            if k not in case:
                errors.append(f"{f_name}: Missing case key '{k}'")

        nba = data.get("next_best_actions", {})
        for k in required_nba_keys:
            if k not in nba:
                errors.append(f"{f_name}: Missing next_best_actions key '{k}'")

        sar = data.get("sar", {})
        for k in required_sar_keys:
            if k not in sar:
                errors.append(f"{f_name}: Missing sar key '{k}'")

        if case.get("pattern") not in valid_patterns:
            errors.append(f"{f_name}: Invalid pattern '{case.get('pattern')}'")

        if case.get("status") not in valid_statuses:
            errors.append(f"{f_name}: Invalid status '{case.get('status')}'")

        if case.get("verdict") not in valid_verdicts:
            errors.append(f"{f_name}: Invalid verdict '{case.get('verdict')}'")

        if case.get("pattern") == "undocumented" and len(case.get("pattern_description", "")) < 80:
            errors.append(f"{f_name}: pattern is 'undocumented' but pattern_description is under 80 characters ({len(case.get('pattern_description', ''))} chars)")

        if case.get("verdict") == "legitimate":
            if len(case.get("affected_txn_ids", [])) > 0:
                errors.append(f"{f_name}: verdict is legitimate but affected_txn_ids is not empty")
            if case.get("exposure_usd", 0) != 0:
                errors.append(f"{f_name}: verdict is legitimate but exposure_usd is not 0")
            if sar.get("file") is not False:
                errors.append(f"{f_name}: verdict is legitimate but sar.file is not False")

        if sar.get("file") is True:
            if len(sar.get("narrative", "")) < 50:
                errors.append(f"{f_name}: sar.file is true but narrative is too short")
            if len(sar.get("activity_dates", [])) != 2:
                errors.append(f"{f_name}: sar.file is true but activity_dates must have 2 dates")

    if errors:
        print(f"FAILED: Found {len(errors)} validation errors:")
        for err in errors[:10]:
            print(f"  ? {err}")
        sys.exit(1)
    else:
        print(f"SUCCESS: All {len(files)} case files passed 100% of format and policy schema validation checks!")

if __name__ == "__main__":
    verify_all_cases()
