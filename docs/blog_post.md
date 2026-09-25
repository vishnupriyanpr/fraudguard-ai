# Building FraudGuard AI: Autonomous Fraud Investigation with TigerGraph, GraphRAG, and Groq LPU Frontier Models

**Official Technical Deep-Dive for TigerGraph × Hacker House Goa 2026 (HHGoa)**  
*By Team FraudGuard AI*

---

## 1. Introduction: The Crisis in Modern Fraud Operations

Financial institutions face an unprecedented volume of fraud alerts. Modern real-time fraud scoring models flag hundreds of thousands of transactions daily. However, **a high risk score is not a verdict**—it is merely an invitation to investigate. 

In traditional operations, fraud analysts spend 30 to 90 minutes per case manually stitching together transaction records, inspecting device fingerprints, verifying geographic anomalies, and checking whether past accounts were compromised by the same syndicate. Meanwhile, illicit funds exit the banking perimeter in minutes.

For the **TigerGraph × Hacker House Goa (HHGoa) 2026 Challenge**, we engineered **FraudGuard AI**—an autonomous agentic fraud investigation system that moves beyond naive binary classification into full-lifecycle, defensible case progression. Powered by **TigerGraph's native parallel graph algorithms**, **GraphRAG**, **Groq LPU Frontier Models** (`qwen/qwen3.8-27b` & `openai/gpt-oss-120b`), and **Active Learning Decision Theory** (Shannon Entropy & EVOI), FraudGuard AI investigates alerts, plans evidence gathering, enforces deterministic policy rules, and recommends explainable Next Best Actions with regulatory SAR filings in under a second per case.

---

## 2. System Architecture & The 7-Stage Closed-Loop Lifecycle

FraudGuard AI is structured as a closed-loop agentic workflow designed with zero look-ahead bias:

```
[Trigger Alert] ──► [Stage 1: Ingestion & Temporal Triage] ──► [Stage 2: Bounded TigerGraph Traversal (ts <= T)]
                                                                               │
                                                                               ▼
[Stage 6: Regulatory SAR Synthesis] ◄── [Stage 5: Policy Engine] ◄── [Stage 4: Active Learning & EVOI Compass]
           │                                                                   │
           ▼                                                                   ▼
[Stage 7: Resolution & Memory] ──────────────────────────────────► [Stage 3: GraphRAG & Case Memory Retrieval]
```

### Key Architectural Pillars:

1. **Strict Bounded As-Of Context**: Every graph traversal is strictly bounded by the alert trigger timestamp $T$ (`ts <= as_of_ts`), mathematically guaranteeing zero look-ahead bias and reproducing historical point-in-time state.
2. **Device Profile Normalization**: Rather than treating device parameters as sparse noise, we synthesize deterministic composite device vertices (`DeviceInfo | OS | Browser | Screen Resolution`), enabling instant $k$-hop detection of emulators and shared botnet infrastructure.
3. **GraphRAG Hybrid Precedent Memory**: Combines semantic embeddings of Bank Fraud Policy v1.0 and FinCEN regulations with 5,565 historical closed cases in TigerGraph, grounding every decision in institutional precedent.
4. **Active Learning & Decision Theory**: Integrates Claude Shannon's Information Entropy ($H(p)$) and the Expected Value of Information (EVOI) to quantify whether reaching out to a customer or requesting step-up authentication is economically justified before disturbing the cardholder.
5. **Groq LPU Acceleration**: Generates audit-ready FinCEN Suspicious Activity Reports in ~0.7s utilizing `qwen/qwen3.8-27b` with deterministic offline resilience.

---

## 3. Graph Schema & GSQL Analytics

In tabular relational data, fraudsters hide between rows. In TigerGraph, their relationships are exposed as topological motifs.

### Graph Topography:
- **Vertices**: `HHG_Customer`, `HHG_Card`, `HHG_Transaction`, `HHG_DeviceProfile`, `HHG_BillingRegion`, `HHG_ClosedCase`, `HHG_InvestigationCase`
- **Edges**: `HHG_OWNS`, `HHG_HAS_TRANSACTION`, `HHG_KNOWN_CARD_TRANSACTION`, `HHG_FROM_DEVICE`, `HHG_BILLED_IN`, `HHG_CLOSED_CASE_ON_CARD`

### Core Investigative Algorithms Implemented:
1. **Card Testing Burst Traversal (`detect_card_testing.gsql`)**: Sub-second sliding window query detecting sequences of $\ge 3$ micro-authorizations ($< \$5$) followed by high-dollar cashout transactions within 60 minutes.
2. **Card Not Present & Proxy Analysis**: Evaluates card-not-present online charges against customer baseline spending medians while flagging anonymous/hidden proxy tunnels (`id_23`).
3. **Coordinated Abuse Ring Detection (`detect_coordinated_abuse.gsql`)**: Explores 2-hop bipartite projections from devices to uncover coordinated cross-account strikes sharing identical infrastructure.
4. **Sub-Threshold Structuring Detection**: Uncovers clusters of rapid online transactions deliberately engineered just under the $500 threshold (as demonstrated in `HHG-006` with 4 transactions totaling $1,906.07).

---

## 4. Resolving the 20 Benchmark Cases: Calibrated Empirical Results

FraudGuard AI was evaluated against the official 20 benchmark test cases (`HHG-001` through `HHG-020`):

- **Total Execution Time**: **16.57 seconds** across all 20 cases (**0.83s average latency per case** including live Groq LLM FinCEN synthesis).
- **Cleared Legitimate (6 cases)**: `HHG-001`, `HHG-007`, `HHG-012`, `HHG-018`, `HHG-019`, `HHG-020`. For example, `HHG-018` was an in-person charge identified as a recurring monthly subscription under Rule R7, preventing an unnecessary block.
- **Confirmed Fraud (12 cases)**: `HHG-002`, `HHG-004`, `HHG-006`, `HHG-008`, `HHG-009`, `HHG-010`, `HHG-011`, `HHG-013`, `HHG-014`, `HHG-015`, `HHG-016`, `HHG-017`. Accurately identified card testing (`HHG-017`), new-device takeovers (`HHG-004`, `HHG-010`), sub-threshold structuring (`HHG-006`), and shared emulator proxy rings (`HHG-014`).
- **Uncertain / Escalated (2 cases)**: `HHG-003` (Uncorroborated in-person dispute with normal baseline; Policy R1/R8), `HHG-005` (Conflicting signal requiring analyst escalation under Policy R8).
- **Regulatory FinCEN SAR Filings (5 cases)**: `HHG-004`, `HHG-006`, `HHG-010`, `HHG-014`, `HHG-015` ($1,000+ exposure, structuring, or organized syndicates).
- **Total Fraud Exposure Mitigated**: **$4,614.16 USD**.
- **Schema Validation Score**: **100% PASS** on all 36 schema and policy rules.

---

## 5. Decision Theory: Expected Value of Information (EVOI)

Rather than using ad-hoc thresholds, FraudGuard AI formulates evidence gathering as an optimal Bayesian stopping problem:

### Binary Shannon Entropy:
$$H(p) = -p \log_2(p) - (1-p) \log_2(1-p)$$
When an alert fires at $p=0.50$, uncertainty is maximal ($H=1.00$ bits). The agent stops gathering evidence when uncertainty collapses below $0.24$ bits ($p \ge 0.96$ or $p \le 0.04$).

### Expected Value of Information:
$$\text{EVOI} = \mathbb{E}[\text{Loss}_{\text{uninformed}}] - \mathbb{E}[\text{Loss}_{\text{informed}}] - C_{\text{friction}}$$
If customer verification has an operational/churn friction cost of $C_{\text{friction}} = \$15$, an evidence request is only emitted when $\text{Net EVOI} > 0$. This prevents alert fatigue and preserves customer trust.

---

## 6. What We Learned & What We Would Improve With More Time

### What Worked Exceptionally Well:
- **TigerGraph's Graph Parallelism**: Bounded multi-hop traversal completed in milliseconds, enabling real-time risk contextualization that tabular SQL simply cannot achieve.
- **Groq LPU Inference**: Synthesizing legally defensible SAR narratives in ~0.7s enabled true real-time autonomous regulatory reporting without bottlenecking the pipeline.
- **Precedent Graph Memory**: Querying past closed cases (`find_similar_closed_cases.gsql`) provided instant contextual baselines for recurring merchant categories.

### What We Would Improve With More Time:
1. **Dynamic GNN Embeddings on Savanna**: Train inductive Graph Neural Networks (such as GraphSAGE) directly on TigerGraph Cloud to compute dynamic graph topology embeddings for zero-day fraud syndicate detection.
2. **Automated Feedback Loop from Cardholder 2FA**: Connect the Streamlit UI to real-time Webhook endpoints for bi-directional cardholder SMS/WhatsApp confirmation loops.
3. **Multi-Institution Graph Federated Learning**: Expand the schema to support cross-bank encrypted entity resolution for nationwide money mule tracking.

---

## 7. Conclusion

By combining TigerGraph's high-performance graph database with Groq LPU frontier models and decision-theoretic active learning, **FraudGuard AI** eliminates manual investigation latency, prevents unnecessary cardholder friction on false alarms, and produces audit-ready regulatory filings in seconds. 

The future of fraud fighting is not passive scoring—it is autonomous, graph-grounded investigation.
