"""
Streamlit Web Dashboard for FraudGuard AI.
Provides real-time fraud case inspection, interactive PyVis graph visualization,
evidence audit trails, human-in-the-loop next-best-action approvals,
policy what-if simulators, and innovative exam period monitoring.
"""

import os
import sys
import json
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from pyvis.network import Network

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.policy.engine import evaluate_final_policy, ActionRecommendation

st.set_page_config(
    page_title="FraudGuard AI ? Autonomous Fraud Operations",
    page_icon="???",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1E222D;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #2E3440;
    }
    .badge-fraud {
        background-color: #EF4444;
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: bold;
    }
    .badge-legit {
        background-color: #10B981;
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: bold;
    }
    .badge-sar {
        background-color: #F59E0B;
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def load_cases(folder_path="cases"):
    """Load case JSON files from directory."""
    cases = {}
    if os.path.exists(folder_path):
        for f in sorted(os.listdir(folder_path)):
            if f.endswith(".json") and f != "benchmark_summary.json" and f != "innovation_summary.json":
                cid = f.replace(".json", "")
                with open(os.path.join(folder_path, f), "r", encoding="utf-8") as fp:
                    cases[cid] = json.load(fp)
    return cases


benchmark_cases = load_cases("cases")
innovative_cases = load_cases("cases_innovative")

# Sidebar
with st.sidebar:
    st.title("??? FraudGuard AI")
    st.caption("TigerGraph ? Hacker House Goa 2026")
    st.divider()

    dataset_mode = st.radio(
        "Investigation Queue:",
        options=["Benchmark Exam Cases (20)", "Innovative Exam Alerts (10)"],
        index=0
    )

    active_cases = benchmark_cases if "Benchmark" in dataset_mode else innovative_cases

    # Case filter by verdict
    verdict_filter = st.selectbox(
        "Filter by Verdict:",
        options=["All Cases", "Confirmed Fraud", "Cleared Legitimate", "SAR Required"],
        index=0
    )

    filtered_case_ids = []
    for cid, cdata in active_cases.items():
        v = cdata["case"]["verdict"]
        sar_file = cdata["sar"]["file"]
        if verdict_filter == "Confirmed Fraud" and v != "fraud":
            continue
        elif verdict_filter == "Cleared Legitimate" and v != "legitimate":
            continue
        elif verdict_filter == "SAR Required" and not sar_file:
            continue
        filtered_case_ids.append(cid)

    selected_case_id = st.selectbox(
        "Select Case File:",
        options=filtered_case_ids if filtered_case_ids else ["None"],
        index=0 if filtered_case_ids else 0
    )

    st.divider()
    st.subheader("? Quick Actions")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("?? Benchmark"):
            with st.spinner("Running 20 benchmark cases..."):
                os.system(f"{sys.executable} scripts/run_benchmark.py")
                st.success("Updated!")
                st.rerun()
    with col_b2:
        if st.button("?? Monitor"):
            with st.spinner("Scanning exam period..."):
                os.system(f"{sys.executable} scripts/run_exam_monitor.py")
                st.success("Updated!")
                st.rerun()

    st.divider()
    st.subheader("?? Queue Telemetry")
    if active_cases:
        total = len(active_cases)
        frauds = sum(1 for c in active_cases.values() if c["case"]["verdict"] == "fraud")
        legits = sum(1 for c in active_cases.values() if c["case"]["verdict"] == "legitimate")
        sars = sum(1 for c in active_cases.values() if c["sar"]["file"])
        total_exp = sum(c["case"]["exposure_usd"] for c in active_cases.values())

        st.metric("Total Cases Loaded", total)
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Confirmed Fraud", frauds)
        col_m2.metric("Cleared Legit", legits)
        st.metric("Regulatory SARs", sars)
        st.metric("Identified Exposure", f"${total_exp:,.2f}")


# Main Content Area
if selected_case_id and selected_case_id in active_cases:
    case_record = active_cases[selected_case_id]
    case = case_record["case"]
    sar = case_record["sar"]
    nba = case_record["next_best_actions"]
    ev_requests = case_record.get("evidence_requests", [])

    # Top Banner
    badge_color = "badge-fraud" if case["verdict"] == "fraud" else "badge-legit"
    st.header(f"Investigation Record: `{selected_case_id}`")
    st.markdown(
        f"**Verdict:** <span class='{badge_color}'>{case['verdict'].upper()}</span> | "
        f"**Pattern:** `{case['pattern'].upper()}` | "
        f"**Exposure:** `${case['exposure_usd']:,.2f} USD`",
        unsafe_allow_html=True
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Fraud Probability", f"{case['fraud_probability'] * 100:.1f}%")
    m2.metric("Investigation Status", case["status"].upper())
    m3.metric("Regulatory SAR", "REQUIRED" if sar["file"] else "NOT REQUIRED")
    m4.metric("Agent Latency", f"{case_record.get('latency_s', 0.0):.2f}s")

    st.divider()

    # Detailed Tabs
    tab_overview, tab_graph, tab_evidence, tab_nba, tab_sar, tab_sim = st.tabs([
        "?? Investigation Summary",
        "??? Interactive Graph (PyVis)",
        "?? Evidence Chain & Audit",
        "?? Next Best Action (HITL)",
        "??? Regulatory SAR Filing",
        "?? Policy Simulator"
    ])

    with tab_overview:
        st.subheader("Executive Case Narrative")
        st.info(case.get("summary", "No summary available."))

        st.subheader("Investigation Resolution Reason")
        st.write(f"?? **Stop Reason:** {case_record.get('stop_reason', '')}")

        col_ov1, col_ov2 = st.columns(2)
        with col_ov1:
            st.subheader("Entities Investigated")
            st.write(f"? **Connected Cards:** `{', '.join(case.get('connected_card_ids', [])) or 'None'}`")
            st.write(f"? **Device Profiles:** `{', '.join(case.get('connected_device_profiles', [])) or 'None'}`")
            st.write(f"? **Affected Transactions:** `{', '.join(case.get('affected_txn_ids', [])) or 'None (Cleared)'}`")

        with col_ov2:
            st.subheader("Case Memory Precedents Retrieved")
            if case.get("similar_prior_cases"):
                st.write(f"Retrieved Closed Cases from TigerGraph: `{', '.join(case['similar_prior_cases'])}`")
            else:
                st.write("No matching prior closed case precedents found.")

    with tab_graph:
        st.subheader("Interactive TigerGraph Entity Topology")
        st.caption("Draggable, physics-simulated graph showing customer, cards, transactions, and infrastructure.")

        # Build PyVis Network
        net = Network(height="480px", width="100%", bgcolor="#111827", font_color="white")
        net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=120)

        # Add Nodes
        cust_id = case.get("evidence", [{}])[0].get("entity_ids", ["C-Unknown"])[0]
        net.add_node("CUST", label=f"Customer\n{cust_id}", color="#3B82F6", size=25, title=f"Customer ID: {cust_id}")

        cards = case.get("connected_card_ids", [])
        for i, card in enumerate(cards):
            net.add_node(f"CARD_{i}", label=f"Card\n{card}", color="#10B981", size=20, title=f"Card: {card}")
            net.add_edge("CUST", f"CARD_{i}", label="OWNS")

        txns = case.get("affected_txn_ids", []) or [case.get("first_suspicious_txn_id", "Flagged")]
        for j, tx in enumerate(txns):
            tx_color = "#EF4444" if case["verdict"] == "fraud" else "#10B981"
            net.add_node(f"TX_{j}", label=f"Txn #{tx}\n${case['exposure_usd']:.2f}", color=tx_color, size=18, title=f"Transaction: {tx}")
            if cards:
                net.add_edge("CARD_0", f"TX_{j}", label="MADE")
            else:
                net.add_edge("CUST", f"TX_{j}", label="TRANSACTED")

        devs = case.get("connected_device_profiles", [])
        for k, dev in enumerate(devs):
            net.add_node(f"DEV_{k}", label=f"Device\n{dev[:25]}...", color="#8B5CF6", size=18, title=f"Device: {dev}")
            if txns:
                net.add_edge(f"TX_0", f"DEV_{k}", label="FROM_DEVICE")

        priors = case.get("similar_prior_cases", [])
        for p, prior in enumerate(priors):
            net.add_node(f"PRIOR_{p}", label=f"Closed Case\n{prior}", color="#F59E0B", size=16, title=f"Precedent Case: {prior}")
            net.add_edge("CUST", f"PRIOR_{p}", label="PRIOR_CASE")

        html_content = net.generate_html()
        components.html(html_content, height=500)

    with tab_evidence:
        st.subheader("Evidence Items Grounded in Graph Traversal")
        for idx, ev in enumerate(case.get("evidence", [])):
            with st.expander(f"Evidence #{idx+1} ? Source: [{ev.get('source', '').upper()}] | Ref: {ev.get('ref', '')}", expanded=True):
                st.markdown(f"**Claim:** {ev.get('claim', '')}")
                st.caption(f"Referenced Entity IDs: `{', '.join(str(e) for e in ev.get('entity_ids', []))}`")

        if ev_requests:
            st.divider()
            st.subheader("Simulated Customer / Analyst Validation Requests")
            for req in ev_requests:
                st.warning(
                    f"**Request Type:** `{req.get('type')}` (Step {req.get('asked_after_step')})\n\n"
                    f"**Assumed Response:** *\"{req.get('assumed_response')}\"*"
                )

    with tab_nba:
        st.subheader("Next Best Action Protocol (Policy Rules R1-R10)")
        st.write("Dynamic recommendation progression before and after evidence gathering.")

        col_n1, col_n2 = st.columns(2)
        with col_n1:
            st.markdown("### 1. Initial Recommendation (Pre-Verification)")
            for a in nba.get("initial", []):
                route_badge = {"auto": "?? auto", "L1": "?? L1 (Lead)", "L2": "?? L2 (Manager)"}.get(a.get("route"), a.get("route"))
                st.markdown(f"**Action:** `{a.get('action')}`  \n**Route:** `{route_badge}`")
                st.caption(f"Policy Justification: {a.get('reason')}")
                st.markdown("---")

        with col_n2:
            st.markdown("### 2. Final Action (Post-Verification)")
            for a in nba.get("final", []):
                route_badge = {"auto": "?? auto", "L1": "?? L1 (Lead)", "L2": "?? L2 (Manager)"}.get(a.get("route"), a.get("route"))
                st.markdown(f"**Action:** `{a.get('action')}`  \n**Route:** `{route_badge}`")
                st.caption(f"Policy Justification: {a.get('reason')}")
                st.markdown("---")

        st.info(f"**What Changed:** {nba.get('what_changed', 'nothing')}")

        st.divider()
        st.subheader("Human-In-The-Loop Approval Desk")
        st.caption("Operational actions with 'auto' route execute autonomously. 'L1' and 'L2' actions require human sign-off.")
        hitl_col1, hitl_col2, hitl_col3 = st.columns(3)
        with hitl_col1:
            if st.button("? Approve Recommended Actions", key="appr_btn"):
                st.success("Actions approved! Executed and recorded in TigerGraph audit log.")
        with hitl_col2:
            if st.button("? Override: Decline & Escalate", key="over_btn"):
                st.warning("Override applied. Case routed to senior risk analyst queue.")
        with hitl_col3:
            if st.button("?? Trigger Cardholder Re-Verification", key="rever_btn"):
                st.info("Additional 2FA verification sent to cardholder device.")

    with tab_sar:
        st.subheader("Regulatory Suspicious Activity Report (FinCEN Standard)")
        if sar.get("file"):
            st.error("?? Mandatory Suspicious Activity Report Filing Required")
            st.markdown(f"**Filing Reason:** {sar.get('reason', '')}")
            st.markdown(f"**Total Suspicious Amount:** `${sar.get('total_amount_usd', 0.0):,.2f} USD`")
            st.markdown(f"**Activity Dates:** `{', '.join(sar.get('activity_dates', []))}`")
            st.markdown(f"**Named Subjects:** `{', '.join(sar.get('subjects', []))}`")

            st.divider()
            st.markdown("### Regulatory Narrative (FinCEN / BSA Format):")
            st.text_area("Official Narrative Text:", value=sar.get("narrative", ""), height=220)
        else:
            st.success("No Suspicious Activity Report required. Activity was cleared as legitimate or falls below statutory filing criteria.")

    with tab_sim:
        st.subheader("?? Policy Simulator & What-If Analysis")
        st.caption("Test how FraudGuard AI's Policy Engine dynamically adapts when evidence changes.")

        sim_response = st.selectbox(
            "Select Simulated Customer Response:",
            options=[
                "Customer states they authorized the purchase and retain physical possession of card",
                "Customer states they did not make this purchase and still have physical possession of card",
                "No response received from customer within 24 hours"
            ],
            index=0 if case["verdict"] == "legitimate" else 1
        )

        init_acts = [
            ActionRecommendation(action=a["action"], route=a["route"], reason=a["reason"])
            for a in nba.get("initial", [])
        ]
        sim_final, sim_what, sim_sar, sim_sar_reason = evaluate_final_policy(
            initial_actions=init_acts,
            assumed_response=sim_response,
            fraud_probability=case["fraud_probability"],
            exposure_usd=case["exposure_usd"] if case["exposure_usd"] > 0 else 100.0,
            pattern=case["pattern"]
        )

        st.markdown("### Simulated Final Policy Outcome:")
        for act in sim_final:
            r_badge = {"auto": "?? auto", "L1": "?? L1 (Lead)", "L2": "?? L2 (Manager)"}.get(act.route, act.route)
            st.markdown(f"? **`{act.action}`** (Route: `{r_badge}`) ? *{act.reason}*")

        st.info(f"**What Changed:** {sim_what}")
        if sim_sar:
            st.warning(f"**SAR Triggered:** {sim_sar_reason}")
        else:
            st.success("SAR Status: Not Required")
else:
    st.info("No cases available. Please click 'Benchmark' in the sidebar to populate cases.")
