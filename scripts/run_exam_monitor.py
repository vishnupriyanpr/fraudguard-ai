"""
CLI Runner for Autonomous Exam Period Monitor.
Scans November-December 2016 for alerts, runs investigations,
and outputs to cases_innovative/.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agent.exam_monitor import ExamPeriodFraudMonitor

def main():
    print("=================================================================")
    print("  ?? FraudGuard AI ? Autonomous Exam Period Monitor (Innovation) ")
    print("=================================================================\n")
    monitor = ExamPeriodFraudMonitor(data_dir="data", output_dir="cases_innovative")
    monitor.monitor_and_investigate(limit=10)

if __name__ == "__main__":
    main()
