"""
InvestigationState and Pydantic validation schemas for FraudGuard AI.
Matches 100% of the IEEE-CIS / HHGoa Answer Format specification.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


class EvidenceEntry(BaseModel):
    claim: str
    source: Literal["graph", "document", "customer", "external"]
    ref: str
    entity_ids: List[str] = Field(default_factory=list)


class CaseDetail(BaseModel):
    status: Literal["open", "closed_fraud", "closed_legitimate", "escalated"]
    verdict: Literal["fraud", "legitimate", "uncertain"]
    fraud_probability: float
    pattern: Literal[
        "card_testing",
        "card_not_present_fraud",
        "card_not_present_new_device",
        "out_of_region_use",
        "account_takeover",
        "undocumented",
        "none"
    ]
    pattern_description: str = ""
    affected_txn_ids: List[str] = Field(default_factory=list)
    first_suspicious_txn_id: str = ""
    connected_card_ids: List[str] = Field(default_factory=list)
    connected_device_profiles: List[str] = Field(default_factory=list)
    exposure_usd: float = 0.0
    evidence: List[EvidenceEntry] = Field(default_factory=list)
    similar_prior_cases: List[str] = Field(default_factory=list)
    summary: str = ""
    written_to_graph: bool = True
    graph_case_id: str = ""


class EvidenceRequest(BaseModel):
    type: Literal["customer_validation", "step_up_auth", "analyst_info"]
    asked_after_step: int
    assumed_response: str


class ActionItem(BaseModel):
    action: str
    route: Literal["auto", "L1", "L2"]
    reason: str


class NextBestActions(BaseModel):
    initial: List[ActionItem] = Field(default_factory=list)
    final: List[ActionItem] = Field(default_factory=list)
    what_changed: str = "nothing"


class SARDetail(BaseModel):
    file: bool
    reason: str
    narrative: str = ""
    subjects: List[str] = Field(default_factory=list)
    total_amount_usd: float = 0.0
    activity_dates: List[str] = Field(default_factory=list)


class CaseSubmissionFormat(BaseModel):
    case_id: str
    case: CaseDetail
    evidence_requests: List[EvidenceRequest] = Field(default_factory=list)
    next_best_actions: NextBestActions
    sar: SARDetail
    stop_reason: str
    tool_calls: int = 0
    tokens: int = 0
    latency_s: float = 0.0


# LangGraph State representation
from typing import TypedDict

class InvestigationState(TypedDict, total=False):
    # Trigger parameters
    case_id: str
    opened_at: str
    trigger_type: str
    trigger_text: str
    flagged_txn_id: str
    card_id: str
    customer_id: str
    risk_score: Optional[float]

    # Graph Extraction & Context
    as_of_timestamp: str
    flagged_txn_data: Dict[str, Any]
    customer_history: List[Dict[str, Any]]
    customer_baseline: Dict[str, Any]
    card_history: List[Dict[str, Any]]
    device_data: Dict[str, Any]
    device_neighbors: List[Dict[str, Any]]
    billing_region_data: Dict[str, Any]

    # Analysis & Anomalies
    amount_deviation: float
    is_new_device: bool
    is_new_region: bool
    is_anonymous_proxy: bool
    is_card_testing: bool
    testing_txns: List[str]
    is_recurring_charge: bool
    is_mixed_channel_48h: bool
    connected_cards: List[str]
    connected_devices: List[str]
    shared_device_detected: bool

    # GraphRAG & Case Memory
    similar_cases: List[Dict[str, Any]]
    similar_case_ids: List[str]
    matched_policies: List[Dict[str, Any]]

    # Evidence & Probabilities
    evidence_list: List[Dict[str, Any]]
    assessed_pattern: str
    pattern_description: str
    fraud_probability: float
    affected_txn_ids: List[str]
    exposure_usd: float
    verdict: str
    status: str

    # Actions & Iteration
    iteration: int
    initial_actions: List[Dict[str, Any]]
    evidence_requests: List[Dict[str, Any]]
    assumed_response: str
    final_actions: List[Dict[str, Any]]
    what_changed: str

    # SAR
    sar_required: bool
    sar_reason: str
    sar_narrative: str
    sar_subjects: List[str]
    sar_dates: List[str]

    # Final Summary & Output
    summary: str
    stop_reason: str
    tool_calls: int
    tokens: int
    latency_s: float
    written_to_graph: bool
    graph_case_id: str
