# 🎬 FraudGuard AI — 3-5 Minute Demo Video Script
### Official Walkthrough for TigerGraph × Hacker House Goa 2026 (HHGoa)

- **Target Video Length**: 3.5 to 4.5 minutes
- **Recording Tool**: Loom, OBS Studio, or Screen Studio (Full HD 1080p)
- **Goal**: Walk through the end-to-end autonomous agent, demonstrate TigerGraph knowledge graph integration, explain Shannon Entropy & EVOI Decision Compass, show Groq LPU FinCEN SAR drafting, and highlight the benchmark validation.

---

### Segment 1 [0:00 – 0:45] — Introduction & The Problem
- **On Screen**: Streamlit Dashboard header (`FraudGuard AI — Autonomous Fraud Operations`).
- **Narration**:
  > *"Hello everyone! Welcome to FraudGuard AI, our autonomous fraud investigation agent built for the TigerGraph × Hacker House Goa 2026 Challenge.*
  > *In financial institutions today, fraud teams are overwhelmed. A machine learning risk score flags hundreds of thousands of transactions daily. But a risk score isn't a verdict. An analyst must manually trace connections, inspect device fingerprints, verify customer baselines, review policy, and draft regulatory filings.*
  > *This manual process takes 30 to 90 minutes per case. By the time an analyst acts, the money is already gone. FraudGuard AI completely automates this investigation lifecycle using TigerGraph, GraphRAG, Groq LPU frontier models, and Active Learning Decision Theory."*

---

### Segment 2 [0:45 – 1:30] — Case HHG-001: Avoiding False Positives with Graph Context
- **On Screen**: Select `HHG-001` in the sidebar. Show metrics: Score 0.61, Amount $77.07. Click on `Interactive Graph (PyVis)` and `Evidence Chain & Audit`.
- **Narration**:
  > *"Let's examine our first benchmark case: HHG-001. An in-person transaction for $77.07 was flagged with an elevated risk score of 0.61 in billing region 444.0.*
  > *A naive automated rule would block this customer's card. But watch what FraudGuard AI does:*
  > *It executes a bounded as-of GSQL query into TigerGraph pulling the customer's prior 360 transactions. It discovers that region 444.0 is part of their normal shopping routine, and $77.07 represents a 0.9x deviation from their median spend.*
  > *Under Bank Policy Rule R1, because probability is under 0.70 with no secondary signals, the agent requests customer verification. Once confirmed, it executes `CLOSE_NO_FRAUD` under Rule R3. Zero customer churn, zero false positive block."*

---

### Segment 3 [1:30 – 2:20] — Case HHG-006 & HHG-010: High-Value Takeover & Sub-Threshold Structuring
- **On Screen**: Toggle to `HHG-006` and then `HHG-010`. Show the `Regulatory SAR Filing` tab with the orange `⚡ Synthesized via Groq LPU (qwen/qwen3.8-27b)` badge.
- **Narration**:
  > *"Now let's see how FraudGuard AI detects complex attacks that bypass standard threshold rules.*
  > *In Case HHG-006, the agent uncovers an undocumented pattern: sub-threshold structuring. Four rapid online purchases within 30 minutes, each deliberately structured just below the $500 internal review threshold ($478.95, $456.96, $488.04, $482.12), totaling $1,906.07.*
  > *Under Policy Section 3a, because exposure exceeds $1,000, a mandatory FinCEN Suspicious Activity Report is required.*
  > *Switching to the SAR tab, you can see FraudGuard AI interfaced with Groq's high-speed LPU running `qwen/qwen3.8-27b` to synthesize an audit-ready FinCEN narrative in just 0.7 seconds, perfectly covering the 5 Ws and H: Who, What, When, Where, Why, and How."*

---

### Segment 4 [2:20 – 3:15] — Active Learning, EVOI Decision Compass & 3D Pareto Optimization
- **On Screen**: Click the `📐 EVOI & Decision Compass` tab. Show the Shannon Entropy curve and the 3D Pareto Counterfactual Decision Frontier.
- **Narration**:
  > *"What truly differentiates FraudGuard AI is its mathematical rigor. Under the EVOI Decision Compass tab, the agent uses Shannon Binary Entropy to measure uncertainty:*
  > *When an alert starts, entropy is at maximum (1.00 bits). The agent only stops investigating when uncertainty collapses below 0.24 bits.*
  > *Furthermore, before sending an SMS verification or disturbing a cardholder, the agent calculates the Expected Value of Information (EVOI). If the expected loss prevented does not exceed the customer friction cost ($15), outreach is suppressed.*
  > *On the right, our 3D Pareto optimizer evaluates candidate action portfolios across Loss Prevented, Customer Convenience, and Regulatory Compliance, picking the Pareto-optimal next-best action."*

---

### Segment 5 [3:15 – 3:55] — Innovation Track: Autonomous Exam Period Streaming Monitor
- **On Screen**: Switch sidebar to `Innovative Exam Alerts (10)`. Click on `INV-001` or show the PyVis ring visualization.
- **Narration**:
  > *"Beyond the 20 benchmark cases, FraudGuard AI addresses the hackathon's Innovation objective by continuously monitoring the final two-month exam period on its own.*
  > *Our Autonomous Exam Period Monitor scanned thousands of unflagged November and December transactions, identifying 10 emerging fraud clusters and coordinated device hops stored in `cases_innovative/`.*
  > *Every investigation is written back into TigerGraph case memory as a permanent vertex to inform future investigations."*

---

### Segment 6 [3:55 – 4:30] — Terminal Verification & Conclusion
- **On Screen**: Switch to terminal/PowerShell. Run `python scripts/verify_submission.py` and `python -m pytest tests/`.
- **Narration**:
  > *"Finally, let's look at engineering quality. We run our strict verification script: all 20 benchmark case files pass 100% of format and policy schema checks. Running pytest, all 9 unit tests pass in 0.02 seconds.*
  > *In total, FraudGuard AI analyzed all 20 cases in just 16.57 seconds, identified $4,614.16 in fraud exposure, cleared 6 legitimate accounts, escalated 2 uncertain cases, and filed 5 regulatory SARs.*
  > *Thank you for watching FraudGuard AI — autonomous, defensible fraud investigation powered by TigerGraph."*
