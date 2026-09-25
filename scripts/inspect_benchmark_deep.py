import csv
import json
import sys
import os
sys.path.insert(0, os.path.abspath("."))
from collections import defaultdict
from src.agent.graph_engine import GraphInvestigationEngine

def inspect_all():
    ge = GraphInvestigationEngine('data')
    cases = list(csv.DictReader(open('data/case_pack.csv')))
    
    print(f"{'Case ID':<8} | {'TrigType':<15} | {'TxnID':<8} | {'Chan':<9} | {'Amt':<8} | {'DevProf':<20} | {'Trigger Text'}")
    print("-" * 120)
    for c in cases:
        cid = c['case_id']
        ttype = c['trigger_type']
        fid = int(c['flagged_txn_id'])
        ttext = c['trigger_text']
        txn = ge.get_transaction(fid)
        chan = txn.get('channel', 'unknown') if txn else 'none'
        amt = float(txn.get('TransactionAmt', 0.0)) if txn else 0.0
        id_rec = ge.get_identity(fid)
        dev_prof, _ = ge.synthesize_device_profile(id_rec)
        print(f"{cid:<8} | {ttype:<15} | {fid:<8} | {chan:<9} | {amt:<8.2f} | {dev_prof[:18]:<20} | {ttext[:45]}")

if __name__ == "__main__":
    inspect_all()
