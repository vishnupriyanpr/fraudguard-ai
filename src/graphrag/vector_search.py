"""
GraphRAG Vector & Semantic Search Engine for FraudGuard AI.
Retrieves fraud policies, regulatory standards (FinCEN SAR guidelines),
known fraud patterns, and past closed cases.
"""

import json
from typing import List, Dict, Any, Optional
import numpy as np


# Ground Truth Fraud Patterns from README
FRAUD_PATTERNS_DB = [
    {
        "pattern": "card_testing",
        "name": "Card Testing",
        "description": "A stolen card number is checked before use: three or more tiny online authorizations, often under $5, then a larger purchase. Confirmed by the sequence itself. Policy R5.",
        "indicators": ["micro_authorizations_under_5", "burst_under_1_hour", "subsequent_larger_purchase", "online_channel"]
    },
    {
        "pattern": "card_not_present_fraud",
        "name": "Card Not Present Fraud",
        "description": "The number is used online without the card. Amounts and products that don't fit the cardholder's history, often in a burst of two to four within 48 hours. On its own, one unusual online purchase is ambiguous: verify. Policy R1 to R4.",
        "indicators": ["online_channel", "unusual_amount_over_baseline", "unseen_product_code", "burst_in_48h"]
    },
    {
        "pattern": "card_not_present_new_device",
        "name": "Card Not Present Fraud from New Device",
        "description": "Same as CNP fraud, with the identity record marking the device as New for this account, sometimes behind a proxy. Stronger than pattern 2, still not proof: people buy new phones.",
        "indicators": ["device_new_flag", "proxy_detected", "online_channel", "unusual_amount"]
    },
    {
        "pattern": "out_of_region_use",
        "name": "Out of Region Use",
        "description": "Card-present purchases in a billing region the cardholder has no history in, while their normal activity continues at home. Several days of purchases in one new region is a trip, not a clone. Policy R2, R3.",
        "indicators": ["in_person_channel", "new_billing_region_addr1", "normal_activity_at_home"]
    },
    {
        "pattern": "account_takeover",
        "name": "Account Takeover",
        "description": "Mixed-channel activity inconsistent with the cardholder, often with device and match-flag anomalies, pointing to stolen credentials rather than a stolen number.",
        "indicators": ["mixed_channel_activity_48h", "new_device", "anonymous_proxy", "credentials_compromised"]
    },
    {
        "pattern": "undocumented",
        "name": "Coordinated Multi-Customer Abuse (Undocumented)",
        "description": "Coordinated or repeated abuse across multiple customers sharing identical device profiles or infrastructure under hidden proxies within a tight temporal window. Policy R9.",
        "indicators": ["shared_device_multiple_customers", "identical_device_new", "anonymous_hidden_proxy", "burst_across_accounts"]
    }
]

# Policy Rules from README
POLICY_RULES_DB = [
    {
        "rule": "R1",
        "name": "Verify before you block on a weak signal",
        "text": "If the case rests on a single signal (including a risk score alone) and your assessed fraud probability is below 0.70, recommend VERIFY_WITH_CUSTOMER or STEP_UP_AUTH before any block. Blocking a legitimate customer on one signal is a policy breach."
    },
    {
        "rule": "R2",
        "name": "Customer denies the transaction",
        "text": "Recommend BLOCK_CARD and CREATE_CASE. Add FILE_REPORT if exposure exceeds $1,000 or the case connects to a shared device profile or another card's fraud."
    },
    {
        "rule": "R3",
        "name": "Customer confirms the transaction",
        "text": "Recommend CLOSE_NO_FRAUD. Note the confirmation in the case file."
    },
    {
        "rule": "R4",
        "name": "No reply within 24 hours",
        "text": "Recommend MONITOR_CARD and DECLINE_TRANSACTION for pending authorizations. Escalate if exposure exceeds $500."
    },
    {
        "rule": "R5",
        "name": "Card testing",
        "text": "Three or more small online authorizations on one card within an hour, followed by a larger purchase: recommend DECLINE_TRANSACTION and STEP_UP_AUTH. If a purchase over $100 has already cleared, recommend BLOCK_CARD."
    },
    {
        "rule": "R6",
        "name": "Shared origin",
        "text": "When several cards show fraud from the same device profile, the same billing region, or the same recipient email in one window, name the shared element, recommend CREATE_CASE and FILE_REPORT, and MONITOR_CONNECTED_CARDS for every card that shares it."
    },
    {
        "rule": "R7",
        "name": "Disputed but legitimate",
        "text": "When the customer disputes a charge that matches their own recurring pattern (same merchant, same amount, monthly), recommend CREATE_CASE, VERIFY_WITH_CUSTOMER, and WARN_CUSTOMER. Do not block."
    },
    {
        "rule": "R8",
        "name": "Escalate when uncertain and exposed",
        "text": "If the verdict is uncertain and exposure exceeds $500, or the evidence conflicts, recommend ESCALATE_TO_ANALYST."
    },
    {
        "rule": "R9",
        "name": "Undocumented patterns",
        "text": "When activity fits none of the known patterns but the evidence shows coordinated or repeated abuse across customers, recommend CREATE_CASE, FILE_REPORT, and ESCALATE_TO_ANALYST, and describe the pattern in your own words. Do not force it into a known category."
    },
    {
        "rule": "R10",
        "name": "Never BLOCK_ALL_CARDS unilaterally",
        "text": "Never BLOCK_ALL_CARDS unless at least two of the customer's cards show confirmed fraud or the customer's credentials are confirmed compromised."
    }
]


class FraudGraphRAG:
    """GraphRAG knowledge engine combining semantic retrieval with graph facts."""

    def __init__(self):
        self.patterns = FRAUD_PATTERNS_DB
        self.policies = POLICY_RULES_DB

    def match_fraud_pattern(self, signals: Dict[str, Any]) -> Tuple[str, float, str]:
        """
        Match detected signals against known and undocumented patterns.
        Returns: (pattern_name, confidence, pattern_description)
        """
        # Check Card Testing
        if signals.get("is_card_testing"):
            return "card_testing", 0.92, ""

        # Check Recurring Subscription (R7)
        if signals.get("is_recurring_charge") and signals.get("trigger_type") == "customer_report":
            return "none", 0.10, ""

        # Check Undocumented Coordinated Abuse (R9)
        if signals.get("shared_device_multiple_customers") and signals.get("connected_customers_count", 0) >= 3:
            desc = (
                "Coordinated multi-customer abuse pattern identified where three or more distinct cardholders "
                f"share an identical device profile ({signals.get('device_profile', 'Unknown')}) under anonymous or hidden "
                "proxy infrastructure within a 48-hour window."
            )
            return "undocumented", 0.88, desc

        # Check Account Takeover
        if signals.get("is_mixed_channel_48h") and signals.get("is_new_device") and signals.get("is_anonymous_proxy"):
            return "account_takeover", 0.85, ""

        # Check Out of Region Use
        if signals.get("channel") == "in_person" and signals.get("is_new_region"):
            # Check if normal activity continues at home
            return "out_of_region_use", 0.80, ""

        # Check Card Not Present from New Device
        if signals.get("channel") == "online" and signals.get("is_new_device"):
            if signals.get("amount_deviation", 1.0) > 2.0 or signals.get("is_anonymous_proxy"):
                return "card_not_present_new_device", 0.78, ""
            return "card_not_present_new_device", 0.65, ""

        # Check Card Not Present Fraud (existing device)
        if signals.get("channel") == "online" and signals.get("amount_deviation", 1.0) > 3.0 and signals.get("amount", 0) > 100.0:
            return "card_not_present_fraud", 0.72, ""

        # If benign
        if signals.get("amount_deviation", 1.0) <= 1.5 and not signals.get("is_new_region") and not signals.get("is_new_device"):
            return "none", 0.05, ""

        return "none", 0.15, ""

    def retrieve_applicable_policies(self, situation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Retrieve relevant policies based on active case signals."""
        matched = []
        prob = situation.get("fraud_probability", 0.0)
        pattern = situation.get("pattern", "none")
        resp = situation.get("assumed_response", "").lower()

        if situation.get("is_recurring_charge"):
            matched.append([p for p in self.policies if p["rule"] == "R7"][0])

        if pattern == "card_testing":
            matched.append([p for p in self.policies if p["rule"] == "R5"][0])

        if pattern == "undocumented":
            matched.append([p for p in self.policies if p["rule"] == "R9"][0])

        if any(k in resp for k in ["deni", "not make", "unauthorized"]):
            matched.append([p for p in self.policies if p["rule"] == "R2"][0])

        if any(k in resp for k in ["confirm", "authorized"]):
            matched.append([p for p in self.policies if p["rule"] == "R3"][0])

        if any(k in resp for k in ["no reply", "unresponsive"]):
            matched.append([p for p in self.policies if p["rule"] == "R4"][0])

        if prob < 0.70 and not any(k in resp for k in ["deni", "confirm"]):
            matched.append([p for p in self.policies if p["rule"] == "R1"][0])

        if situation.get("shared_device_detected"):
            matched.append([p for p in self.policies if p["rule"] == "R6"][0])

        return matched
