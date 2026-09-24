# ?? FraudGuard AI ? 3-5 Minute Demo Video Script

## Video Overview
- **Length**: ~3.5 to 4.5 minutes
- **Format**: Screen recording with voiceover (Loom or OBS)
- **Goal**: Demonstrate how FraudGuard AI autonomously investigates fraud cases from the HHGoa IEEE-CIS dataset, uses TigerGraph topology, enforces policy rules R1-R10, and generates compliant SARs.

---

### [0:00 - 0:45] Introduction & The Problem
- **Visual**: Show Streamlit Dashboard header (`FraudGuard AI ? Autonomous Fraud Investigation`).
- **Narration**: 
  *"Welcome! This is FraudGuard AI, our autonomous fraud investigation agent built for the TigerGraph Hacker House Goa 2026 challenge. Financial institutions are overwhelmed by fraud alerts?often driven by real-time risk scores that flag thousands of false alarms every day. A high risk score isn't a verdict. An analyst must manually trace connections, inspect devices, check customer history, and apply bank policies. FraudGuard AI automates this entire lifecycle using TigerGraph, GraphRAG, and LangGraph."*

---

### [0:45 - 1:45] Investigating Case 1: The False Alarm (HHG-001)
- **Visual**: Select `HHG-001` in the sidebar. Show metrics: Score 0.61, Amount $77.07, Channel in_person. Click on `Entity Knowledge Graph` and `Evidence Chain`.
- **Narration**:
  *"Let's look at Case HHG-001. The bank's real-time model scored transaction 3514030 at 0.61 in billing region 444.0. A traditional automated rule might block this card. But watch what FraudGuard AI does:*
  *It executes a bounded as-of graph query into TigerGraph to pull the customer's prior 360 transactions. It discovers that region 444.0 is already part of the customer's normal shopping history, and $77.07 is right around their median spend of $83.*
  *Under Policy Rule R1, the agent requests customer verification. The customer confirms, and the agent executes `CLOSE_NO_FRAUD` under Rule R3. Zero customer friction, zero false positive block."*

---

### [1:45 - 2:45] Investigating Case 10: High-Value Takeover & SAR Filing (HHG-010)
- **Visual**: Select `HHG-010`. Show metrics: Amount $1,000.03, Median $76.00 (13.2x deviation), New Device. Click on `Next Best Action` and `Regulatory SAR Filing`.
- **Narration**:
  *"Now let's examine Case HHG-010. This is a dramatic $1,000.03 online transaction?a 13.2x deviation from the customer's $76 baseline. The identity record reveals a brand new device profile.*
  *When verified, the customer denies authorizing the purchase. Watch the Next Best Action panel: the recommendation dynamically escalates from initial verification to BLOCK_CARD, formal case creation, and because exposure exceeds $1,000, Policy 3a mandates a regulatory filing.*
  *Switching to the SAR tab, you can see FraudGuard AI automatically drafted a full FinCEN-compliant Suspicious Activity Report with exact dates, subject identifiers, amounts, and investigative narrative."*

---

### [2:45 - 3:30] Investigating Case 14 & 18: Coordinated Rings and Subscriptions
- **Visual**: Quickly toggle `HHG-018` (Recurring charge, R7) and `HHG-014` (Undocumented coordinated ring, R9).
- **Narration**:
  *"FraudGuard AI handles the subtle cases that rule-based systems get wrong. In HHG-018, a disputed in-person charge is recognized as a recurring monthly subscription under Rule R7, prompting a customer reminder rather than an aggressive block.*
  *In HHG-014, an analyst probe across multiple accounts reveals a coordinated fraud ring sharing an identical Android emulator profile behind an anonymous proxy. The agent classifies this as an undocumented pattern under Rule R9 and routes it directly to senior management."*

---

### [3:30 - 4:00] Execution Speed & Submission Deliverables
- **Visual**: Show `cases/` directory in VS Code or Terminal with all 20 JSON files and run `python scripts/verify_submission.py`.
- **Narration**:
  *"All 20 benchmark cases run in just 11.4 seconds. Running our submission verification script confirms that all 20 case files adhere 100% to the challenge schema, with audit-ready case memory, initial and final next-best actions, and complete SARs.*
  *Thank you for watching FraudGuard AI?autonomous fraud operations powered by TigerGraph."*
