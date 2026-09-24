"""
Unit tests for FraudGuard AI Policy Engine (Rules R1-R10).
"""

import pytest
from src.policy.engine import (
    evaluate_initial_policy,
    evaluate_final_policy,
    get_approval_route,
    ROUTE_AUTO,
    ROUTE_L1,
    ROUTE_L2
)


def test_approval_routing():
    assert get_approval_route("ALLOW_TRANSACTION") == ROUTE_AUTO
    assert get_approval_route("DECLINE_TRANSACTION") == ROUTE_L1
    assert get_approval_route("BLOCK_CARD", exposure_usd=500.0) == ROUTE_L1
    assert get_approval_route("BLOCK_CARD", exposure_usd=3000.0) == ROUTE_L2
    assert get_approval_route("BLOCK_ALL_CARDS") == ROUTE_L2
    assert get_approval_route("FILE_REPORT") == ROUTE_L2


def test_rule_r1_weak_signal_verification():
    actions = evaluate_initial_policy(
        fraud_probability=0.45,
        pattern="card_not_present_fraud",
        exposure_usd=150.0,
        is_single_signal=True,
        trigger_type="risk_score"
    )
    action_names = [a.action for a in actions]
    assert "VERIFY_WITH_CUSTOMER" in action_names
    assert "BLOCK_CARD" not in action_names


def test_rule_r2_customer_denial():
    initial_actions = evaluate_initial_policy(
        fraud_probability=0.65,
        pattern="card_not_present_fraud",
        exposure_usd=250.0,
        is_single_signal=False
    )
    final_actions, what_changed, sar_file, sar_reason = evaluate_final_policy(
        initial_actions=initial_actions,
        assumed_response="Customer states they did not make this purchase and still have physical possession of card",
        fraud_probability=0.65,
        exposure_usd=250.0,
        pattern="card_not_present_fraud"
    )
    action_names = [a.action for a in final_actions]
    assert "BLOCK_CARD" in action_names
    assert "CREATE_CASE" in action_names
    assert "Customer confirmed unauthorized" in what_changed


def test_rule_r3_customer_confirmation():
    initial_actions = evaluate_initial_policy(
        fraud_probability=0.50,
        pattern="none",
        exposure_usd=75.0,
        is_single_signal=True
    )
    final_actions, what_changed, sar_file, sar_reason = evaluate_final_policy(
        initial_actions=initial_actions,
        assumed_response="Customer confirms they authorized the charge",
        fraud_probability=0.50,
        exposure_usd=75.0,
        pattern="none"
    )
    action_names = [a.action for a in final_actions]
    assert "CLOSE_NO_FRAUD" in action_names
    assert sar_file is False


def test_rule_r5_card_testing():
    actions = evaluate_initial_policy(
        fraud_probability=0.85,
        pattern="card_testing",
        exposure_usd=280.0,
        is_single_signal=False,
        card_testing_detected=True,
        card_testing_large_purchase_cleared=True
    )
    action_names = [a.action for a in actions]
    assert "DECLINE_TRANSACTION" in action_names
    assert "STEP_UP_AUTH" in action_names
    assert "BLOCK_CARD" in action_names


def test_rule_r7_recurring_subscription():
    actions = evaluate_initial_policy(
        fraud_probability=0.20,
        pattern="none",
        exposure_usd=39.08,
        is_single_signal=False,
        is_recurring_dispute=True
    )
    action_names = [a.action for a in actions]
    assert "CREATE_CASE" in action_names
    assert "VERIFY_WITH_CUSTOMER" in action_names
    assert "WARN_CUSTOMER" in action_names
    assert "BLOCK_CARD" not in action_names


def test_rule_r9_undocumented_pattern():
    actions = evaluate_initial_policy(
        fraud_probability=0.90,
        pattern="undocumented",
        exposure_usd=500.0,
        is_single_signal=False,
        is_undocumented_pattern=True
    )
    action_names = [a.action for a in actions]
    assert "CREATE_CASE" in action_names
    assert "FILE_REPORT" in action_names
    assert "ESCALATE_TO_ANALYST" in action_names
