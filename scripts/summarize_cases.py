import json
import glob

def summarize():
    files = sorted(glob.glob("cases/HHG-*.json"))
    print(f"Total case files: {len(files)}")
    print(f"{'Case ID':<9} | {'Verdict':<11} | {'Pattern':<28} | {'Prob':<6} | {'Exposure':<10} | {'EvReq':<6} | {'SAR':<10}")
    print("-" * 95)
    for f in files:
        with open(f, "r", encoding="utf-8") as fp:
            d = json.load(fp)
        cid = d.get("case_id", "")
        c = d["case"]
        verd = c.get("verdict", "unknown")
        patt = c.get("pattern", "none")
        prob = f"{c.get('fraud_probability', 0.0):.2f}"
        exp = f"${c.get('exposure_usd', 0.0):.2f}"
        ev = len(d.get("evidence_requests", []))
        sar = d.get("sar", {}).get("decision", "none")
        print(f"{cid:<9} | {verd:<11} | {patt:<28} | {prob:<6} | {exp:<10} | {ev:<6} | {sar:<10}")

if __name__ == "__main__":
    summarize()
