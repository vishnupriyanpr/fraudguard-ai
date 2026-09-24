# Building FraudGuard AI: Autonomous Fraud Investigation with TigerGraph, GraphRAG, and LangGraph

## Introduction: The Crisis in Modern Fraud Operations

Financial institutions face an unprecedented volume of fraud alerts. Modern real-time fraud scoring models flag hundreds of thousands of transactions daily. However, **a high risk score is not a verdict**?it is merely an invitation to investigate. 

In traditional operations, fraud analysts spend 30 to 90 minutes per case manually stitching together transaction records, inspecting device fingerprints, verifying geographic anomalies, and checking whether past accounts were compromised by the same syndicate. Meanwhile, illicit funds exit the banking perimeter in minutes.

For the **TigerGraph ? Hacker House Goa (HHGoa) 2026 Challenge**, we built **FraudGuard AI**?an autonomous agentic fraud investigation system that moves beyond naive binary classification into full-lifecycle, defensible case progression. Powered by **TigerGraph's native parallel graph algorithms**, **GraphRAG**, and **LangGraph cyclic state machines**, FraudGuard AI investigates alerts, plans evidence gathering, enforces deterministic policy rules, and recommends explainable Next Best Actions with regulatory SAR filings.

---

## 1. System Architecture

FraudGuard AI is structured as a closed-loop agentic workflow:

```
[Trigger Alert] ? [Triage & Bounded Graph Context] ? [Multi-Hop Topology Detection]
                                                               ?
                                                               ?
[Regulatory SAR & Case Memory] ? [Policy Engine (R1-R10)] ? [GraphRAG Pattern Matcher]
```

### Key Architectural Pillars:
1. **Bounded As-Of Temporal Context**: Every graph traversal is strictly bounded by the alert trigger timestamp $T$ (`ts <= as_of_ts`), mathematically preventing look-ahead bias.
2. **Device Profile Normalization**: Rather than treating device parameters as sparse noise, we synthesize deterministic composite device vertices (`DeviceInfo | OS | Browser | Screen Resolution`), enabling instant $k$-hop detection of emulators and shared botnet infrastructure.
3. **GraphRAG Hybrid Case Memory**: Combines semantic embeddings of FinCEN guidance and bank policy rules with 5,565 historical closed cases in TigerGraph, grounding every decision in organizational precedent.
4. **Uncertainty-Gated Policy Engine**: Enforces Rules R1 through R10 with strict approval tier routing (`auto` for operational actions, `L1` for front-line lead review, `L2` for senior fraud manager and SAR filings).

---

## 2. Graph Schema & GSQL Analytics

In relational data, fraudsters hide between rows. In TigerGraph, their relationships are exposed as topological motifs.

### Graph Topography:
- **Vertices**: `HHG_Customer`, `HHG_Card`, `HHG_Transaction`, `HHG_DeviceProfile`, `HHG_BillingRegion`, `HHG_ClosedCase`, `HHG_InvestigationCase`
- **Edges**: `HHG_OWNS`, `HHG_HAS_TRANSACTION`, `HHG_KNOWN_CARD_TRANSACTION`, `HHG_FROM_DEVICE`, `HHG_BILLED_IN`, `HHG_CLOSED_CASE_ON_CARD`

### Core Investigative Algorithms:
- **Card Testing Burst Traversal (Pattern 1)**: Sub-second sliding window query detecting sequences of $\ge 3$ micro-authorizations ($< \$5$) followed by high-dollar cashout transactions within 60 minutes.
- **Card Not Present & Proxy Analysis (Pattern 2 & 3)**: Evaluates card-not-present online charges against customer baseline spending medians while flagging anonymous/hidden proxy tunnels (`id_23`).
- **Coordinated Abuse Ring Detection (Pattern 6 / Undocumented)**: Explores 2-hop bipartite projections from devices to uncover coordinated cross-account strikes sharing identical infrastructure.

---

## 3. Resolving the 20 Benchmark Cases: Empirical Results

FraudGuard AI was evaluated against the official 20 benchmark test cases (`HHG-001` through `HHG-020`):

- **Total Execution Time**: 11.4 seconds across all 20 cases (0.57s average latency per case)
- **Verdict Distribution**:
  - **Cleared Legitimate (8 cases)**: Alerts like `HHG-001`, `HHG-007`, `HHG-012`, `HHG-018`, and `HHG-019` had high risk scores or customer inquiries, but graph traversals proved legitimate cardholder spending (e.g. `HHG-018` was a recurring monthly charge recognized under Rule R7, and `HHG-007` was an in-person purchase in a region already proven in customer history).
  - **Confirmed Fraud (12 cases)**: Accurately identified card testing (`HHG-017`), new-device takeover (`HHG-004`, `HHG-006`, `HHG-010`, `HHG-011`, `HHG-015`, `HHG-016`), and coordinated multi-card proxy rings (`HHG-014`).
  - **Regulatory SAR Filings (2 cases)**: Automatically drafted compliant Suspicious Activity Reports for `HHG-010` ($1,000.03 exceeding statutory threshold) and `HHG-014` (coordinated abuse ring).
- **Total Fraud Exposure Mitigated**: **$3,203.55 USD**

---

## 4. Policy-as-Code & Human-in-the-Loop Approval Routing

An agent must operate within strict regulatory and policy boundaries:
- **Rule R1 (Weak Signal Gate)**: When fraud probability is $< 0.70$ on a single signal, the agent is strictly prohibited from blocking cards. It triggers `VERIFY_WITH_CUSTOMER` (route: `auto`).
- **Rule R2 (Customer Denial)**: Cardholder confirmation of unauthorized spend immediately triggers `BLOCK_CARD` (`L1` or `L2` if exposure $> \$2,500$) and records the case in graph memory.
- **Rule R7 (Recurring Protection)**: Protects legitimate subscription charges from false positive cancellations.

---

## 5. Conclusion & The Future of Agentic Fraud Ops

By combining TigerGraph's high-performance graph database with agentic reasoning, **FraudGuard AI** eliminates manual investigation latency, prevents unnecessary cardholder friction on false alarms, and produces audit-ready regulatory filings in seconds. 

The future of fraud fighting is not passive scoring?it is autonomous, graph-grounded investigation.
