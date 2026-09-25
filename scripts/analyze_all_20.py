import csv
import json
import sys
import os
from datetime import datetime, timedelta
from statistics import median

sys.path.insert(0, os.path.abspath("."))
from src.agent.graph_engine import GraphInvestigationEngine

def parse_ts(v):
    return datetime.strptime(str(v)[:19], "%Y-%m-%d %H:%M:%S")

def analyze_all_20():
    ge = GraphInvestigationEngine('data')
    cases = list(csv.DictReader(open('data/case_pack.csv')))
    
    print(f"{'Case':<8} | {'Trig':<15} | {'Chan':<7} | {'Amt':<8} | {'DevProf':<22} | {'New?':<5} | {'Proxy':<10} | {'Structuring?':<12} | {'Burst48h':<8} | {'DevCards30d':<11}")
    print("-" * 125)
    
    for c in cases:
        cid = c['case_id']
        ttype = c['trigger_type']
        fid = int(c['flagged_txn_id'])
        txn = ge.get_transaction(fid)
        chan = txn.get('channel', 'unknown') if txn else 'none'
        amt = float(txn.get('TransactionAmt', 0.0)) if txn else 0.0
        t0 = parse_ts(txn['ts'])
        
        id_rec = ge.get_identity(fid)
        dev_prof, _ = ge.synthesize_device_profile(id_rec)
        is_new_dev_flag = (str(id_rec.get('id_15', '')).lower() == 'new') if id_rec else False
        proxy_type = str(id_rec.get('id_23', '')) if id_rec else ''
        
        # Check customer transactions
        cust_txns = ge.get_customer_transactions(c['customer_id'], c['opened_at'])
        
        # Check structuring: near 400-500 within 60 mins
        near_struct = [t for t in cust_txns if 400.0 <= float(t.get('TransactionAmt', 0)) <= 500.0 and abs((parse_ts(t['ts']) - t0).total_seconds()) <= 3600]
        is_struct = len(near_struct) >= 2
        
        # Check burst 48h
        near_48h = [t for t in cust_txns if abs((parse_ts(t['ts']) - t0).total_seconds()) <= 48 * 3600]
        burst_cnt = len(near_48h)
        
        # Check device sharing within 30 days
        dev_cards_30d = 0
        if dev_prof:
            all_dev_txns = ge.txns_by_device_profile.get(dev_prof, [])
            cards_30d = set()
            for tid in all_dev_txns:
                t = ge.get_transaction(tid)
                if t and abs((parse_ts(t['ts']) - t0).total_seconds()) <= 30 * 86400:
                    cards_30d.add(t.get('card_id'))
            dev_cards_30d = len(cards_30d)
            
        print(f"{cid:<8} | {ttype:<15} | {chan:<7} | {amt:<8.2f} | {dev_prof[:20]:<22} | {str(is_new_dev_flag):<5} | {proxy_type[:9]:<10} | {str(is_struct):<12} | {burst_cnt:<8} | {dev_cards_30d:<11}")

if __name__ == "__main__":
    analyze_all_20()
