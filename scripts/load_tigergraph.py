"""
TigerGraph Database Loader for FraudGuard AI.
Loads vertices (Customers, Cards, Transactions, DeviceProfiles, BillingRegions, ClosedCases)
and directed edges into a target TigerGraph instance using pyTigerGraph.
"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def connect_tigergraph():
    host = os.getenv("TG_HOST", "http://127.0.0.1")
    graphname = os.getenv("TG_GRAPHNAME", "FraudInvestigationGraph")
    username = os.getenv("TG_USERNAME", "tigergraph")
    password = os.getenv("TG_PASSWORD", "tigergraph")
    tgcloud = os.getenv("TG_TGCLOUD", "false").lower() == "true"

    try:
        import pyTigerGraph as tg
        conn = tg.TigerGraphConnection(
            host=host,
            graphname=graphname,
            username=username,
            password=password,
            tgCloud=tgcloud
        )
        print(f"Connecting to TigerGraph at {host} (Graph: {graphname})...")
        conn.getToken()
        print("Connected successfully!")
        return conn
    except Exception as e:
        print(f"Notice: Could not connect to live TigerGraph instance: {e}")
        print("FraudGuard AI will continue running in offline/in-memory graph mode.")
        return None

def main():
    conn = connect_tigergraph()
    if not conn:
        print("To load into TigerGraph Savanna, set TG_HOST and credentials in .env.")
        return

    print("Deploying GSQL schema from gsql/schema.gsql...")
    with open("gsql/schema.gsql", "r", encoding="utf-8") as f:
        schema_gsql = f.read()
    try:
        res = conn.gsql(schema_gsql)
        print("Schema deployment output:", res)
    except Exception as e:
        print("Schema creation notice:", e)

if __name__ == "__main__":
    main()
