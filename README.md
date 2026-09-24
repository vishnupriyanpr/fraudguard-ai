# ??? FraudGuard AI ? TigerGraph Agentic Fraud Investigation System
### Official Submission for TigerGraph ? Hacker House Goa 2026 (HHGoa)

> **Autonomous agent for fraud investigation, case progression, policy-grounded Next Best Action (NBA) recommendation, and regulatory SAR generation powered by TigerGraph and GraphRAG.**

---

## ?? Executive Summary

FraudGuard AI transforms reactive fraud scoring into an **autonomous, evidence-driven investigation system**. Operating over the full **IEEE-CIS Fraud Detection dataset** (~590,000 transactions, 144,000 identity records, and 5,565 historical closed cases), FraudGuard AI:

1. **Investigates** alerts from initial trigger through multi-hop topological graph analysis to defensible resolution.
2. **Quantifies Uncertainty** to avoid blocking legitimate customers on weak single signals (Policy Rule R1).
3. **Recommends Next Best Actions (NBA)** with explicit approval routing (`auto`, `L1` Lead, `L2` Manager) that dynamically evolve as new evidence arrives.
4. **Drafts Regulatory SAR Filings** meeting FinCEN standards when statutory thresholds ($1,000+) or coordinated syndicates are identified.
5. **Maintains Case Memory** in TigerGraph so past investigations inform future decisions.

---

## ?? Benchmark Results (The 20 Exam Cases)

All 20 official benchmark test cases (`HHG-001` through `HHG-020`) were investigated and validated against the challenge schema:

- **Total Execution Time**: **11.40 seconds** (0.57s average per case)
- **Cleared as Legitimate (8 cases)**: `HHG-001`, `HHG-005`, `HHG-007`, `HHG-012`, `HHG-013`, `HHG-018`, `HHG-019`, `HHG-020`
- **Confirmed Fraud (12 cases)**: `HHG-002`, `HHG-003`, `HHG-004`, `HHG-006`, `HHG-008`, `HHG-009`, `HHG-010`, `HHG-011`, `HHG-014`, `HHG-015`, `HHG-016`, `HHG-017`
- **Total Fraud Exposure Identified**: **$3,203.55 USD**
- **Regulatory SARs Filed**: 2 (`HHG-010` and `HHG-014`)
- **Schema Validation Score**: **100% PASS** (Validated via `scripts/verify_submission.py`)

All answer files are located in `cases/` and mirrored in `output/benchmark_cases/`.

---

## ??? System Architecture

```
                                  +------------------------------+
                                  | Alert Trigger (Score/Report) |
                                  +------------------------------+
                                                 |
                                                 v
                                  +------------------------------+
                                  | 1. Bounded As-Of Context     |
                                  |    (Customer History <= T)   |
                                  +------------------------------+
                                                 |
                                                 v
                                  +------------------------------+
                                  | 2. Multi-Hop Graph Traversal |
                                  |    (Device/Region/Testing)   |
                                  +------------------------------+
                                                 |
                                                 v
      +--------------------+      +------------------------------+
      |  Case Memory &     | <--> | 3. GraphRAG Pattern Matcher  |
      |  Closed Cases DB   |      |    (Policies & 5+1 Typology) |
      +--------------------+      +------------------------------+
                                                 |
                                                 v
                                  +------------------------------+
                                  | 4. Initial NBA Evaluation    |
                                  |    (Rules R1-R10, Weak Signal)|
                                  +------------------------------+
                                                 |
                                                 v
                                  +------------------------------+
                                  | 5. Human-in-the-Loop Sim     |
                                  |    (Verify with Cardholder)  |
                                  +------------------------------+
                                                 |
                                                 v
                                  +------------------------------+
                                  | 6. Final Policy & Actions    |
                                  |    (auto / L1 / L2 Routing)  |
                                  +------------------------------+
                                                 |
                                                 v
                                  +------------------------------+
                                  | 7. SAR Narrative & Case File |
                                  |    (FinCEN Format + Output)  |
                                  +------------------------------+
```

---

## ?? Quick Start Guide

### 1. Prerequisites & Environment Setup
```bash
# Clone the repository
git clone https://github.com/your-username/fraudguard-ai.git
cd fraudguard-ai

# Install dependencies (Python 3.10-3.14 supported)
pip install -r requirements.txt
```

### 2. Verify Dataset
Ensure the hackathon data files are located in `data/`:
- `data/transactions.csv` (708 MB)
- `data/identity.csv` (26 MB)
- `data/closed_cases_history.csv` (2.7 MB)
- `data/case_pack.csv` (3.5 KB)
- `data/README.md` (38 KB)

### 3. Run Benchmark Suite (20 Cases)
```bash
python scripts/run_benchmark.py
```
This generates:
- `cases/HHG-001.json` through `cases/HHG-020.json`
- `output/benchmark_cases/` mirror
- `output/benchmark_cases/benchmark_summary.json`

### 4. Verify Submission Schema Compliance
```bash
python scripts/verify_submission.py
```
Outputs:
`SUCCESS: All 20 case files passed 100% of format and policy schema validation checks!`

### 5. Launch Streamlit Investigation Dashboard
```bash
streamlit run src/ui/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser to interactively explore cases, view graph networks, audit evidence, and test human approval actions.

---

## ?? Project Repository Structure

```
??? cases/                        # Primary submission folder: 20 benchmark JSON answer files
?   ??? HHG-001.json
?   ??? ...
?   ??? HHG-020.json
?
??? data/                         # IEEE-CIS dataset files
?   ??? case_pack.csv
?   ??? closed_cases_history.csv
?   ??? identity.csv
?   ??? README.md
?   ??? transactions.csv
?
??? docs/                         # Technical documentation & submission collateral
?   ??? blog_post.md              # Complete technical blog post
?   ??? demo_script.md            # 3-5 minute demo video walkthrough script
?
??? gsql/                         # TigerGraph DDL & GSQL Queries
?   ??? schema.gsql               # Full schema definition with reverse edges
?   ??? queries/
?
??? output/
?   ??? benchmark_cases/          # Output backup and benchmark_summary.json
?
??? scripts/
?   ??? load_tigergraph.py        # TigerGraph Cloud / Savanna loader
?   ??? run_benchmark.py          # Benchmark runner (all 20 cases)
?   ??? verify_submission.py      # Schema and policy validator
?
??? src/
?   ??? agent/
?   ?   ??? graph_engine.py       # High-performance in-memory graph traversal & indexing
?   ?   ??? investigator.py       # Autonomous 7-stage investigation lifecycle agent
?   ?   ??? state.py              # Pydantic schemas & TypedDict state definitions
?   ?
?   ??? graphrag/
?   ?   ??? vector_search.py      # Semantic matcher for fraud patterns and policy rules
?   ?
?   ??? memory/
?   ?   ??? case_memory.py        # Case memory manager linking past and live cases
?   ?
?   ??? policy/
?   ?   ??? engine.py             # Fraud Policy Engine (Rules R1-R10, auto/L1/L2 routing)
?   ?
?   ??? ui/
?       ??? app.py                # Streamlit interactive investigation dashboard
?
??? .env.example                  # Environment configuration template
??? README.md                     # Main repository guide (this file)
??? requirements.txt              # Project dependencies
```

---

## ?? Fraud Policy & Approval Matrix

| Action | Route | Applied When | Customer Impact |
|---|---|---|---|
| `ALLOW_TRANSACTION` | `auto` | Legitimate baseline, no anomaly | None |
| `DECLINE_TRANSACTION` | `L1` | Card testing, or customer unconfirmed | Low |
| `MONITOR_CARD` | `auto` | Weak signal, 72h elevated monitoring | None |
| `MONITOR_CONNECTED_CARDS` | `auto` | Shared device profile or ring detected (R6) | None |
| `WARN_CUSTOMER` | `auto` | Recurring charge clarification (R7) | None |
| `VERIFY_WITH_CUSTOMER` | `auto` | Single signal, probability < 0.70 (R1) | Low |
| `STEP_UP_AUTH` | `auto` | Require OTP after testing attempts (R5) | Low |
| `BLOCK_CARD` | `L1` / `L2` | Customer denial (R2). `L1` if ? $2,500; `L2` if > $2,500 | High |
| `BLOCK_ALL_CARDS` | `L2` | Multi-card compromise confirmed (R10) | Very High |
| `CREATE_CASE` | `auto` | Internal case record written to graph (3a) | None |
| `FILE_REPORT` | `L2` | Exposure > $1,000, shared ring, or undocumented | None |
| `ESCALATE_TO_ANALYST` | `auto` | Uncertain verdict & exposure > $500 (R8) | None |
| `CLOSE_NO_FRAUD` | `auto` | Customer confirmed authorized charge (R3) | None |

---

## ?? Hackathon Alignment

- **Accuracy**: 6 graph detection criteria, bounded as-of queries, zero look-ahead bias.
- **Explainability**: Full evidence chain citing graph queries and entity IDs in every case file.
- **Policy Enforcement**: Rules R1 to R10 strictly enforced with exact action identifiers and routing tiers.
- **SAR Generation**: Complete narratives covering who, what, when, where, how, and why.
- **Case Memory**: Persisted in graph and retrieved for subsequent investigations.
- **Sub-Second Speed**: High-performance multi-threaded graph traversal evaluating all 20 cases in ~11 seconds.

*Developed for the TigerGraph ? Hacker House Goa 2026 Challenge.*
