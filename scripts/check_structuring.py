import sys, os, csv
sys.path.insert(0, os.path.abspath('.'))
from src.agent.graph_engine import GraphInvestigationEngine
from datetime import datetime, timedelta

def check_all():
    ge = GraphInvestigationEngine('data')
    cases = list(csv.DictReader(open('data/case_pack.csv')))
    for c in cases:
        fid = int(c['flagged_txn_id'])
        txn = ge.get_transaction(fid)
        amt = float(txn['TransactionAmt'])
        txns = ge.get_customer_transactions(c['customer_id'], c['opened_at'])
        t0 = datetime.strptime(txn['ts'][:19], '%Y-%m-%d %H:%M:%S')
        near = [t for t in txns if abs((datetime.strptime(t['ts'][:19], '%Y-%m-%d %H:%M:%S') - t0).total_seconds()) <= 3600 and 400.0 <= float(t['TransactionAmt']) <= 500.0]
        if len(near) >= 2 or 400.0 <= amt <= 500.0:
            print(f"{c['case_id']}: flagged amt={amt}, chan={txn['channel']}, struct_txns={len(near)}")
            for t in near:
                print(f"   {t['TransactionID']} amt={t['TransactionAmt']} {t['ts']} {t['channel']}")

if __name__ == "__main__":
    check_all()
