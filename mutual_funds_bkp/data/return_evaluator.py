import statistics
import sys
import os
from pymongo import UpdateOne
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db import mutual_funds_collection

def fetch_funds():
    mutual_funds = mutual_funds_collection.find()
    mutual_funds_list = []
    for fund in mutual_funds:
        fund["_id"] = str(fund["_id"])
        mutual_funds_list.append(fund)
    return mutual_funds_list

def evaluate_returns_100():
    funds = fetch_funds()
    horizons = ["1y", "3y", "5y"]

    # 1) Collect diffs separately for positives and negatives
    pos_excess = {h: [] for h in horizons}
    neg_excess = {h: [] for h in horizons}
    for f in funds:
        for h in horizons:
            diff = f["returns"][h]["investment"] - f["returns"][h]["category"]
            if diff >= 0:
                pos_excess[h].append(diff)
            else:
                neg_excess[h].append(diff)

    # 2) Determine max positive and most negative excess per horizon
    max_pos = {h: (max(pos_excess[h]) if pos_excess[h] else 0.0) or 1.0 for h in horizons}
    min_neg = {h: (min(neg_excess[h]) if neg_excess[h] else 0.0) for h in horizons}

    evaluated = []
    for f in funds:
        scores = {}
        for h in horizons:
            diff = f["returns"][h]["investment"] - f["returns"][h]["category"]
            if diff >= 0:
                # scale 0→max_pos to 0→100
                scores[h] = (diff / max_pos[h]) * 100
            else:
                # scale min_neg→0 to -100→0
                # diff/min_neg is in [0,1], multiply by -100 to get negative range
                if min_neg[h] != 0:
                    scores[h] = (diff / min_neg[h]) * -100
                else:
                    scores[h] = 0.0

        # equally weight horizons
        overall = sum(scores.values()) / len(horizons)

        evaluated.append({
            "name": f["name"],
            "scores": scores,             # e.g. {"1y":  45.2, "3y": -12.6, "5y":  80.1}
            "overall_score": overall      # can be negative if losses dominate
        })

    # sort by descending overall (highest net return score first)
    return sorted(evaluated, key=lambda x: x["overall_score"], reverse=True)

def push_return_scores():
    evaluated = evaluate_returns_100()  
    ops = []
    for f in evaluated:
        ops.append(
            UpdateOne(
                {"name": f["name"]},                        # match by fund name
                {"$set": {
                    "return_score": f["overall_score"],               # store overall score
                }},
                upsert=False                                 # or True if you want to insert missing docs
            )
        )
    # 3) send them in one bulk_write
    if ops:
        result = mutual_funds_collection.bulk_write(ops)
        print(f"Matched:  {result.matched_count}")
        print(f"Modified: {result.modified_count}")

if __name__ == "__main__":
    push_return_scores()
    print("Return scores updated successfully.")
