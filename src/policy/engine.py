"""
Fraud Policy Engine for FraudGuard AI.
Strictly implements Fraud Policy Version 1.0 from the TigerGraph HHGoa challenge:
- 14 distinct actions
- Approval routing tiers: auto, L1, L2
- Rules R1 to R10
- Exact SAR requirement determination per Policy 3a & R2/R6/R9
"""

from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel

VALID_ACTIONS = {
    "ALLOW_TRANSACTION",
    "DECLINE_TRANSACTION",
    "MONITOR_CARD",
    "MONITOR_CONNECTED_CARDS",
    "WARN_CUSTOMER",
    "VERIFY_WITH_CUSTOMER",
    "STEP_UP_AUTH",
    "BLOCK_CARD",
    "BLOCK_ALL_CARDS",
    "GENERATE_REPORT",
    "CREATE_CASE",
    "FILE_REPORT",
    "ESCALATE_TO_ANALYST",
    "CLOSE_NO_FRAUD",
}

ROUTE_AUTO = "auto"
ROUTE_L1 = "L1"
ROUTE_L2 = "L2"


class ActionRecommendation(BaseModel):
    action: str
    route: str
    reason: str


def get_approval_route(action: str, exposure_usd: float = 0.0) -> str:
    """
    Approval routing per Section 2:
    - auto: ALLOW_TRANSACTION, MONITOR_CARD, MONITOR_CONNECTED_CARDS, WARN_CUSTOMER,
            VERIFY_WITH_CUSTOMER, STEP_UP_AUTH, GENERATE_REPORT, CREATE_CASE,
            ESCALATE_TO_ANALYST, CLOSE_NO_FRAUD
    - L1: DECLINE_TRANSACTION; BLOCK_CARD when exposure <= $2,500
    - L2: BLOCK_CARD when exposure > $2,500; BLOCK_ALL_CARDS always; FILE_REPORT always
    """
    if action == "DECLINE_TRANSACTION":
        return ROUTE_L1
    elif action == "BLOCK_CARD":
        return ROUTE_L2 if exposure_usd > 2500.0 else ROUTE_L1
    elif action in ("BLOCK_ALL_CARDS", "FILE_REPORT"):
        return ROUTE_L2
    else:
        return ROUTE_AUTO


def evaluate_initial_policy(
    fraud_probability: float,
    pattern: str,
    exposure_usd: float,
    is_single_signal: bool,
    card_testing_detected: bool = False,
    card_testing_large_purchase_cleared: bool = False,
    is_recurring_dispute: bool = False,
    shared_device_detected: bool = False,
    is_undocumented_pattern: bool = False,
    trigger_type: str = "risk_score",
) -> List[ActionRecommendation]:
    """
    Evaluate initial Next Best Actions before evidence requests return.
    """
    actions: List[ActionRecommendation] = []

    # Rule R7: Recurring charge dispute
    if is_recurring_dispute:
        actions.append(ActionRecommendation(
            action="CREATE_CASE",
            route=ROUTE_AUTO,
            reason="R7: Disputed charge matches recurring monthly cadence and amount"
        ))
        actions.append(ActionRecommendation(
            action="VERIFY_WITH_CUSTOMER",
            route=ROUTE_AUTO,
            reason="R7: Confirm with customer before taking any blocking action"
        ))
        actions.append(ActionRecommendation(
            action="WARN_CUSTOMER",
            route=ROUTE_AUTO,
            reason="R7: Remind customer of potential recurring subscription pattern"
        ))
        return actions

    # Rule R5: Card testing sequence
    if card_testing_detected:
        actions.append(ActionRecommendation(
            action="DECLINE_TRANSACTION",
            route=ROUTE_L1,
            reason="R5: Card testing micro-authorization sequence detected"
        ))
        actions.append(ActionRecommendation(
            action="STEP_UP_AUTH",
            route=ROUTE_AUTO,
            reason="R5: Require step-up passcode verification following testing attempts"
        ))
        if card_testing_large_purchase_cleared:
            route = get_approval_route("BLOCK_CARD", exposure_usd)
            actions.append(ActionRecommendation(
                action="BLOCK_CARD",
                route=route,
                reason=f"R5: Subsequent purchase over $100 has cleared (exposure ${exposure_usd:.2f})"
            ))
        actions.append(ActionRecommendation(
            action="CREATE_CASE",
            route=ROUTE_AUTO,
            reason="Policy 3a: Open case to track card testing attack"
        ))
        return actions

    # Rule R9: Undocumented pattern (coordinated multi-customer abuse)
    if is_undocumented_pattern:
        actions.append(ActionRecommendation(
            action="CREATE_CASE",
            route=ROUTE_AUTO,
            reason="R9: Coordinated multi-customer abuse pattern identified across accounts"
        ))
        actions.append(ActionRecommendation(
            action="FILE_REPORT",
            route=ROUTE_L2,
            reason="R9: Coordinated cross-account abuse requires regulatory filing"
        ))
        actions.append(ActionRecommendation(
            action="ESCALATE_TO_ANALYST",
            route=ROUTE_AUTO,
            reason="R9: Undocumented pattern requires senior analyst review"
        ))
        return actions

    # Rule R1: Verify before blocking on weak / single signal
    if (is_single_signal or trigger_type in ("risk_score", "customer_report")) and fraud_probability < 0.70:
        if trigger_type == "customer_report":
            actions.append(ActionRecommendation(
                action="CREATE_CASE",
                route=ROUTE_AUTO,
                reason="Policy 3a: Customer dispute requires opening an internal case"
            ))
            actions.append(ActionRecommendation(
                action="VERIFY_WITH_CUSTOMER",
                route=ROUTE_AUTO,
                reason="R1: Confirm details of disputed transaction with cardholder"
            ))
        else:
            actions.append(ActionRecommendation(
                action="VERIFY_WITH_CUSTOMER",
                route=ROUTE_AUTO,
                reason="R1: Probability < 0.70 on single signal; verify with cardholder before blocking"
            ))
            if fraud_probability >= 0.30:
                actions.append(ActionRecommendation(
                    action="CREATE_CASE",
                    route=ROUTE_AUTO,
                    reason="Policy 3a: Open internal case as fraud probability reached 0.30"
                ))
            else:
                actions.append(ActionRecommendation(
                    action="MONITOR_CARD",
                    route=ROUTE_AUTO,
                    reason="Policy 1: Place card under 72h elevated monitoring pending verification"
                ))
        return actions

    # Strong signal / high probability before verification
    if fraud_probability >= 0.70:
        if shared_device_detected:
            actions.append(ActionRecommendation(
                action="CREATE_CASE",
                route=ROUTE_AUTO,
                reason="R6: Shared device profile links multiple cards to known fraud"
            ))
            actions.append(ActionRecommendation(
                action="MONITOR_CONNECTED_CARDS",
                route=ROUTE_AUTO,
                reason="R6: Put all cards sharing device under monitoring"
            ))
        else:
            actions.append(ActionRecommendation(
                action="CREATE_CASE",
                route=ROUTE_AUTO,
                reason="Policy 3a: High fraud probability warrants formal case creation"
            ))

        actions.append(ActionRecommendation(
            action="VERIFY_WITH_CUSTOMER",
            route=ROUTE_AUTO,
            reason="R1: Verify with customer to confirm compromise before blocking"
        ))
        return actions

    # Low risk default
    return [
        ActionRecommendation(action="MONITOR_CARD", route=ROUTE_AUTO, reason="Low suspicion; raise monitoring sensitivity"),
        ActionRecommendation(action="ALLOW_TRANSACTION", route=ROUTE_AUTO, reason="No confirmed policy breach")
    ]


def evaluate_final_policy(
    initial_actions: List[ActionRecommendation],
    assumed_response: str,
    fraud_probability: float,
    exposure_usd: float,
    pattern: str,
    shared_device_detected: bool = False,
    is_undocumented_pattern: bool = False,
    compromised_cards_count: int = 1,
    is_recurring_dispute: bool = False,
) -> Tuple[List[ActionRecommendation], str, bool, str]:
    """
    Evaluate final Next Best Actions after assumed customer/analyst response.
    """
    final_actions: List[ActionRecommendation] = []
    sar_file = False
    sar_reason = ""
    what_changed = "nothing"

    resp = assumed_response.lower()

    # Rule R3: Customer confirms transaction
    if any(k in resp for k in ["confirm", "authorized", "legitimate", "yes", "made this", "i made", "recognize"]):
        final_actions.append(ActionRecommendation(
            action="CLOSE_NO_FRAUD",
            route=ROUTE_AUTO,
            reason="R3: Customer confirmed the transaction was authorized"
        ))
        what_changed = (
            "Customer confirmed authorizing the transaction. Assessed fraud probability resolved to legitimate (<=0.05). "
            "Pending verification resolved to CLOSE_NO_FRAUD per Rule R3."
        )
        return final_actions, what_changed, False, ""

    # Rule R2: Customer denies transaction
    elif any(k in resp for k in ["deni", "not make", "unauthorized", "never made", "stolen", "did not", "didnt"]):
        # Rule R10 check: BLOCK_ALL_CARDS if >= 2 cards compromised
        if compromised_cards_count >= 2:
            final_actions.append(ActionRecommendation(
                action="BLOCK_ALL_CARDS",
                route=ROUTE_L2,
                reason=f"R10: Multiple cards ({compromised_cards_count}) confirmed compromised for customer"
            ))
        else:
            route_block = get_approval_route("BLOCK_CARD", exposure_usd)
            final_actions.append(ActionRecommendation(
                action="BLOCK_CARD",
                route=route_block,
                reason=f"R2: Customer denied transaction; exposure ${exposure_usd:.2f} ({'L2' if exposure_usd > 2500 else 'L1'})"
            ))

        final_actions.append(ActionRecommendation(
            action="CREATE_CASE",
            route=ROUTE_AUTO,
            reason="R2: Customer denial confirms unauthorized transaction episode"
        ))

        # SAR check: Policy 3a & R2
        # Exposure > $1,000 OR shared device / other card OR undocumented
        if exposure_usd > 1000.0 or shared_device_detected or is_undocumented_pattern:
            final_actions.append(ActionRecommendation(
                action="FILE_REPORT",
                route=ROUTE_L2,
                reason="R2/Policy 3a: Confirmed fraud with " + (
                    f"exposure ${exposure_usd:.2f} exceeding $1,000 threshold" if exposure_usd > 1000.0
                    else "shared device connecting to multiple compromised cards"
                )
            ))
            sar_file = True
            sar_reason = (
                f"Policy 3a & R2: Confirmed unauthorized activity with total exposure of ${exposure_usd:.2f}"
                + (", exceeding the $1,000 regulatory filing threshold" if exposure_usd > 1000.0 else "")
                + (", linked across shared device infrastructure" if shared_device_detected else "")
            )

        if shared_device_detected:
            final_actions.append(ActionRecommendation(
                action="MONITOR_CONNECTED_CARDS",
                route=ROUTE_AUTO,
                reason="R6: Shared device profile links this compromise to other active cards"
            ))

        what_changed = (
            f"Customer confirmed unauthorized activity. Assessed fraud probability escalated to 0.95+. "
            f"Next actions transitioned to BLOCK_CARD, formal case recording, and "
            f"{'SAR regulatory filing' if sar_file else 'monitoring'}."
        )
        return final_actions, what_changed, sar_file, sar_reason

    # Rule R4: No reply within 24 hours
    elif any(k in resp for k in ["no reply", "unresponsive", "24 hours", "no response"]):
        final_actions.append(ActionRecommendation(
            action="MONITOR_CARD",
            route=ROUTE_AUTO,
            reason="R4: Customer unresponsive after 24h; maintain 72h elevated monitoring"
        ))
        final_actions.append(ActionRecommendation(
            action="DECLINE_TRANSACTION",
            route=ROUTE_L1,
            reason="R4: Decline pending authorizations while cardholder remains unconfirmed"
        ))
        if exposure_usd > 500.0:
            final_actions.append(ActionRecommendation(
                action="ESCALATE_TO_ANALYST",
                route=ROUTE_AUTO,
                reason="R4: Exposure > $500 without customer reply requires human escalation"
            ))

        what_changed = (
            "No response received from cardholder within 24 hours. Under Rule R4, card placed on 72h "
            f"monitoring and pending authorizations declined{' with analyst escalation' if exposure_usd > 500 else ''}."
        )
        return final_actions, what_changed, False, ""

    # Default: No change
    else:
        final_actions = initial_actions
        what_changed = "nothing"
        for act in final_actions:
            if act.action == "FILE_REPORT":
                sar_file = True
                sar_reason = act.reason
        return final_actions, what_changed, sar_file, sar_reason
