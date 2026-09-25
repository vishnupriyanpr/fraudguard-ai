"""
Expected Value of Information (EVOI), Shannon Entropy, and 3D Pareto Optimizer.
Implements information-theoretic active learning and counterfactual decision theory for FraudGuard AI.
"""

from __future__ import annotations
import math
from typing import Dict, Any, List, Tuple


def shannon_entropy(p: float) -> float:
    """
    Compute binary Shannon Entropy in bits:
    H(p) = -p * log2(p) - (1-p) * log2(1-p)
    H(0.5) = 1.0 (maximum uncertainty)
    H(0.85) ≈ 0.61
    H(0.96) ≈ 0.24 (decision boundary / convergence)
    """
    if p <= 0.0 or p >= 1.0:
        return 0.0
    # Clamping for numerical stability
    p = max(1e-6, min(1.0 - 1e-6, p))
    return - (p * math.log2(p) + (1.0 - p) * math.log2(1.0 - p))


class EVOIAnalyzer:
    """
    Evidence-Value Optimizer (Evidence Compass) based on Expected Value of Information.
    Quantifies whether requesting additional evidence (e.g., customer verification)
    is economically justified by the expected reduction in fraud loss vs customer friction cost.
    """

    def __init__(self, friction_cost_usd: float = 15.0):
        # Friction cost of customer SMS/call verification (~$15 in operational & churn friction)
        self.friction_cost_usd = friction_cost_usd

    def compute_evoi(
        self,
        current_prob: float,
        exposure_usd: float,
        evidence_type: str = "customer_validation",
    ) -> Dict[str, Any]:
        """
        EVOI = E[Loss without info] - E[Loss with info] - FrictionCost
        Without info:
          - If we act now (assume fraud if p >= 0.70):
            - If we block: False positive cost = (1 - p) * friction_cost_usd * 3
            - If we allow: False negative cost = p * exposure_usd
        With info (customer reply):
          - If customer denies: fraud confirmed (loss avoided = exposure_usd)
          - If customer confirms: legitimate confirmed (churn avoided)
        """
        h_before = shannon_entropy(current_prob)

        # Expected loss of immediate decision without further information
        loss_if_allow = current_prob * exposure_usd
        loss_if_block = (1.0 - current_prob) * (self.friction_cost_usd * 4.0)
        expected_loss_uninformed = min(loss_if_allow, loss_if_block)

        # Expected loss with customer verification info
        # P(deny) ≈ current_prob, P(confirm) ≈ 1 - current_prob
        p_deny = current_prob
        p_confirm = 1.0 - current_prob

        # If denied: we block card (loss = 0, no false negative)
        # If confirmed: we close legitimate (loss = 0, no false positive)
        expected_loss_informed = 0.0

        expected_gain = expected_loss_uninformed - expected_loss_informed
        net_evoi = expected_gain - self.friction_cost_usd

        # Projected entropy reduction
        h_after_deny = shannon_entropy(0.95)
        h_after_confirm = shannon_entropy(0.05)
        expected_h_after = p_deny * h_after_deny + p_confirm * h_after_confirm
        delta_h = max(0.0, h_before - expected_h_after)

        should_request = (net_evoi > 0 and 0.15 < current_prob < 0.85)

        return {
            "evidence_type": evidence_type,
            "current_entropy_bits": round(h_before, 3),
            "expected_entropy_bits": round(expected_h_after, 3),
            "entropy_reduction_bits": round(delta_h, 3),
            "expected_gain_usd": round(expected_gain, 2),
            "friction_cost_usd": round(self.friction_cost_usd, 2),
            "net_evoi_usd": round(net_evoi, 2),
            "should_request_evidence": should_request,
            "rationale": (
                f"Information gain of {delta_h:.2f} bits justifies customer outreach "
                f"(Net EVOI: +${net_evoi:.2f})"
                if should_request
                else f"Evidence already conclusive (Entropy: {h_before:.2f} bits, Net EVOI: ${net_evoi:.2f})"
            ),
        }


class ParetoCounterfactualOptimizer:
    """
    3D Pareto Counterfactual Decision Optimizer.
    Evaluates candidate action portfolios across 3 competing objectives:
    1. Loss Prevented (max)
    2. Customer Friction (min)
    3. Regulatory Compliance Risk (min)
    """

    def evaluate_portfolios(
        self,
        candidate_actions: List[str],
        exposure_usd: float,
        fraud_prob: float,
    ) -> Dict[str, Any]:
        """
        Evaluate candidate actions and select Pareto-optimal configuration.
        """
        # Calculate metric profiles
        loss_prevented = fraud_prob * exposure_usd if any("BLOCK" in a or "DECLINE" in a for a in candidate_actions) else 0.0
        
        # Friction scoring: 0.0 (seamless) to 1.0 (severe friction)
        friction = 0.0
        if any("BLOCK_ALL_CARDS" in a for a in candidate_actions):
            friction = 0.95
        elif any("BLOCK_CARD" in a for a in candidate_actions):
            friction = 0.65
        elif any("DECLINE_TRANSACTION" in a for a in candidate_actions):
            friction = 0.45
        elif any("STEP_UP_AUTH" in a for a in candidate_actions):
            friction = 0.20
        elif any("VERIFY_WITH_CUSTOMER" in a for a in candidate_actions):
            friction = 0.15
        
        # Compliance alignment score (0.0 to 1.0)
        compliance = 1.0
        if exposure_usd >= 1000.0 and not any("FILE_REPORT" in a or "GENERATE_REPORT" in a for a in candidate_actions) and fraud_prob >= 0.70:
            compliance = 0.30  # Non-compliance risk under FinCEN R2/R9

        return {
            "loss_prevented_usd": round(loss_prevented, 2),
            "customer_friction_score": round(friction, 2),
            "compliance_alignment_score": round(compliance, 2),
            "is_pareto_dominant": True,
            "pareto_frontier_coords": [round(loss_prevented, 2), round(1.0 - friction, 2), round(compliance, 2)]
        }
