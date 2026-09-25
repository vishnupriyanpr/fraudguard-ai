import sys, os, csv
sys.path.insert(0, os.path.abspath('.'))
from src.agent.graph_engine import GraphInvestigationEngine
from datetime import datetime, timedelta

def check_sar_candidates():
    ge = GraphInvestigationEngine('data')
    cases = list(csv.DictReader(open('data/case_pack.csv')))
    
    print(f"{'Case':<8} | {'FlaggedAmt':<11} | {'Burst48hAmt':<12} | {'Win30dAmt':<11} | {'DevCards30d':<11} | {'Notes'}")
    print("-" * 80)
    for c in cases:
        cid = c['case_id']
        fid = int(c['flagged_txn_id'])
        txn = ge.get_transaction(fid)
        amt = float(txn['TransactionAmt'])
        t0 = datetime.strptime(txn['ts'][:19], '%Y-%m-%d %H:%M:%S')
        txns = ge.get_customer_transactions(c['customer_id'], c['opened_at'])
        
        # 48h window on same card
        near_48h = [t for t in txns if abs((datetime.strptime(t['ts'][:19], '%Y-%m-%d %H:%M:%S') - t0).total_seconds()) <= 48 * 3600 and t.get('card_id') == c['card_id']]
        burst_amt = sum(float(t['TransactionAmt']) for t in near_48h)
        
        # 30d window on same card
        win_30d = [t for t in txns if 0 <= (t0 - datetime.strptime(t['ts'][:19], '%Y-%m-%d %H:%M:%S')).total_seconds() <= 30 * 86400 and t.get('card_id') == c['card_id']]
        win_30d_amt = sum(float(t['TransactionAmt']) for t in win_30d)
        
        notes = []
        if cid == 'HHG-006':
            notes.append("sub-threshold structuring")
        if cid == 'HHG-014':
            notes.append("shared emulator ring")
        if amt >= 1000.0 or burst_amt >= 1000.0:
            notes.append(">= $1000 threshold")
            
        print(f"{cid:<8} | ${amt:<10.2f} | ${burst_amt:<11.2f} | ${win_30d_amt:<10.2f} | {' '.join(notes)}")

if __name__ == "__main__":
    check_sar_candidates()
