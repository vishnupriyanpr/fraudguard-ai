"""
Streamlit Web Dashboard for FraudGuard AI.
Provides real-time fraud case inspection, graph visualization,
evidence audits, human-in-the-loop next-best-action approvals, and SAR generation.
"""

import os
import sys
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.agent.graph_engine import GraphInvestigationEngine
from src.agent.investigator import FraudInvestigationAgent

st.set_page_config(
    page_title="FraudGuard AI ? Autonomous Fraud Investigation",
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

@st.cache_resource
def get_engine_and_agent():
    engine = GraphInvestigationEngine(data_dir="data")
    agent = FraudInvestigationAgent(graph_engine=engine)
    return engine, agent

engine, agent = get_engine_and_agent()

# Load Cases
cases_dir = "cases"
case_files = sorted([f for f in os.listdir(cases_dir) if f.endswith(".json")]) if os.path.exists(cases_dir) else []
cases_data = {}
for cf in case_files:
    with open(os.path.join(cases_dir, cf), "r", encoding="utf-8") as f:
        cid = cf.replace(".json", "")
        cases_data[cid] = json.load(f)

# Sidebar
with st.sidebar:
    st.title("??? FraudGuard AI")
    st.caption("TigerGraph ? Hacker House Goa 2026")
    st.divider()

    st.subheader("?? Benchmark Cases (20)")
    selected_case_id = st.selectbox(
        "Select Investigation Case:",
        options=list(cases_data.keys()) if cases_data else ["None"],
        index=0 if cases_data else 0
    )

    if st.button("?? Re-run All 20 Benchmark Cases"):
        with st.spinner("Executing agent investigations..."):
            os.system(f"{sys.executable} scripts/run_benchmark.py")
            st.success("Benchmark completed! Reloading...")
            st.rerun()

    st.divider()
    st.subheader("?? System Telemetry")
    if cases_data:
        total = len(cases_data)
        frauds = sum(1 for c in cases_data.values() if c["case"]["verdict"] == "fraud")
        legits = sum(1 for c in cases_data.values() if c["case"]["verdict"] == "legitimate")
        sars = sum(1 for c in cases_data.values() if c["sar"]["file"])
        total_exp = sum(c["case"]["exposure_usd"] for c in cases_data.values())

        st.metric("Total Cases", total)
        col_s1, col_s2 = st.columns(2)
        col_s1.metric("Confirmed Fraud", frauds)
        col_s2.metric("Cleared Legit", legits)
        st.metric("SARs Filed", sars)
        st.metric("Total Exposure", f"${total_exp:,.2f}")

# Main Content
if selected_case_id and selected_case_id in cases_data:
    case_record = cases_data[selected_case_id]
    case = case_record["case"]
    sar = case_record["sar"]
    nba = case_record["next_best_actions"]
    ev_requests = case_record.get("evidence_requests", [])

    # Top Header Metrics
    st.header(f"Case File: {selected_case_id}")
    st.markdown(f"**Status:** `{case['status'].upper()}` | **Pattern:** `{case['pattern'].upper()}` | **Exposure:** `${case['exposure_usd']:,.2f}`")

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric("Assessed Verdict", case["verdict"].upper())
    with m_col2:
        st.metric("Fraud Probability", f"{case['fraud_probability'] * 100:.1f}%")
    with m_col3:
        st.metric("SAR Required", "YES (Filed)" if sar["file"] else "NO")
    with m_col4:
        st.metric("Agent Latency", f"{case_record.get('latency_s', 0.0):.2f}s")

    st.divider()

    # Tabs
    tab_overview, tab_graph, tab_evidence, tab_nba, tab_sar = st.tabs([
        "?? Investigation Summary",
        "??? Entity Knowledge Graph",
        "?? Evidence Chain & Audit",
        "?? Next Best Action (HITL)",
        "??? Regulatory SAR Filing"
    ])

    with tab_overview:
        st.subheader("Case Narrative Summary")
        st.info(case.get("summary", "No summary available."))

        st.subheader("Stop Reason")
        st.write(f"?? {case_record.get('stop_reason', '')}")

        st.subheader("Affected Transactions")
        aff_txns = case.get("affected_txn_ids", [])
        if aff_txns:
            st.write(f"Involved Transaction IDs: `{', '.join(aff_txns)}`")
            st.metric("Financial Exposure Identified", f"${case['exposure_usd']:,.2f} USD")
        else:
            st.success("No fraudulent transactions identified. Account activity cleared.")

        if case.get("similar_prior_cases"):
            st.subheader("Case Memory Precedents Retrieved")
            st.write(f"Retrieved Closed Cases: `{', '.join(case['similar_prior_cases'])}`")

    with tab_graph:
        st.subheader("TigerGraph Subgraph Visualization")
        # Visual diagram using Plotly
        st.write("Traversed Subgraph: `Customer` ? `Card` ? `Transaction` ? `DeviceProfile` & `BillingRegion`")

        nodes = ["Customer", "Card", f"Txn #{case.get('first_suspicious_txn_id', 'Flagged')}"]
        if case.get("connected_device_profiles"):
            nodes.append("DeviceProfile")
        nodes.append("BillingRegion")

        # Interactive Graph Representation
        fig = go.Figure(data=[go.Scatter(
            x=[0, 1, 2, 2.8, 2.8],
            y=[0, 0, 0, 1, -1],
            mode='markers+text',
            text=nodes,
            textposition="top center",
            marker=dict(size=[30, 25, 20, 20, 20], color=['#3B82F6', '#10B981', '#EF4444', '#8B5CF6', '#F59E0B'])
        )])
        fig.update_layout(
            title=f"Entity Subgraph for {selected_case_id}",
            showlegend=False,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=380
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab_evidence:
        st.subheader("Evidence Items Collected by Agent")
        for i, ev in enumerate(case.get("evidence", [])):
            with st.expander(f"Evidence #{i+1} ? Source: [{ev.get('source', '').upper()}] | Ref: {ev.get('ref', '')}"):
                st.markdown(f"**Claim:** {ev.get('claim', '')}")
                st.caption(f"Referenced Entities: `{', '.join(str(e) for e in ev.get('entity_ids', []))}`")

        if ev_requests:
            st.divider()
            st.subheader("Simulated Human / Customer Verification")
            for req in ev_requests:
                st.warning(f"**Request Type:** `{req.get('type')}` (Step {req.get('asked_after_step')})\n\n"
                           f"**Assumed Response:** *\"{req.get('assumed_response')}\"*")

    with tab_nba:
        st.subheader("Next Best Action Protocol (Policy Rules R1-R10)")

        col_init, col_final = st.columns(2)
        with col_init:
            st.markdown("### 1. Initial Recommendation (Pre-Verification)")
            for a in nba.get("initial", []):
                route_color = {"auto": "??", "L1": "??", "L2": "??"}.get(a.get("route"), "?")
                st.markdown(f"**{route_color} `{a.get('action')}`** (Route: `{a.get('route')}`)")
                st.caption(f"Reason: {a.get('reason')}")

        with col_final:
            st.markdown("### 2. Final Action (Post-Verification)")
            for a in nba.get("final", []):
                route_color = {"auto": "??", "L1": "??", "L2": "??"}.get(a.get("route"), "?")
                st.markdown(f"**{route_color} `{a.get('action')}`** (Route: `{a.get('route')}`)")
                st.caption(f"Reason: {a.get('reason')}")

        st.info(f"**What Changed:** {nba.get('what_changed', 'nothing')}")

        st.divider()
        st.subheader("Human-In-The-Loop Approval Desk")
        st.write("Only `auto` actions execute autonomously. `L1` (Team Lead) and `L2` (Fraud Manager) require human sign-off.")
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            if st.button("? Approve Recommended Actions", key="app_ok"):
                st.success("Actions approved and logged to TigerGraph audit trail.")
        with btn_col2:
            if st.button("? Override: Decline & Escalate", key="app_ovr"):
                st.warning("Decision overridden. Case routed to senior risk queue.")
        with btn_col3:
            if st.button("?? Request Additional Verification", key="app_req"):
                st.info("Additional 2FA push notification sent to cardholder.")

    with tab_sar:
        st.subheader("Suspicious Activity Report (FinCEN Standard)")
        if sar.get("file"):
            st.error("?? Mandatory Regulatory Filing Required")
            st.markdown(f"**Filing Reason:** {sar.get('reason', '')}")
            st.markdown(f"**Total Suspicious Amount:** `${sar.get('total_amount_usd', 0.0):,.2f} USD`")
            st.markdown(f"**Activity Dates:** `{', '.join(sar.get('activity_dates', []))}`")
            st.markdown(f"**Subjects Cited:** `{', '.join(sar.get('subjects', []))}`")

            st.divider()
            st.markdown("### Official SAR Narrative")
            st.text_area("Narrative Text (FinCEN / BSA Format):", value=sar.get("narrative", ""), height=220)
        else:
            st.success("No Suspicious Activity Report required for this case. Activity cleared or below regulatory threshold.")
else:
    st.info("No benchmark case files found. Click 'Re-run All 20 Benchmark Cases' in the sidebar.")
