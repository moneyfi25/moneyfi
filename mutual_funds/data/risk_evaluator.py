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

def compute_expense_median(funds):
    expenses = [float(f['metrics']["expense_ratio"]) for f in funds]
    return statistics.median(expenses)

def risk_score(fund, expense_median):
    m = fund["metrics"]
    score = 0

    # 1) Sharpe Ratio > category average
    if m["sharpe_ratio"]["investment"] <= m["sharpe_ratio"]["category"]:
        score += 1

    # 2) Alpha > 0
    if m["alpha"]["investment"] <= 0:
        score += 1

    # 3) Standard Deviation < category average
    if m["standard_deviation"]["investment"] >= m["standard_deviation"]["category"]:
        score += 1

    # 4) Max Drawdown ≥ -20% (avoid funds with deeper drops)
    if m["maximum_drawdown"] < -0.20:
        score += 1

    # 5) Beta ≤ 1.1 (too-sensitive funds are riskier)
    if m["beta"] > 1.10:
        score += 1

    # 6) Expense Ratio < category median
    if m["expense_ratio"] > expense_median:
        score += 1

    return score

def evaluate_all_risk():
    funds = fetch_funds()
    expense_med = compute_expense_median(funds)

    evaluated = []
    for f in funds:
        s = risk_score(f, expense_med)
        evaluated.append({
            "name": f["name"],
            "score": s,
        })

    return sorted(evaluated, key=lambda x: x["score"])

def push_risk_scores():
    evaluated = evaluate_all_risk()  
    ops = []
    for f in evaluated:
        ops.append(
            UpdateOne(
                {"name": f["name"]},                        # match by fund name
                {"$set": {
                    "risk_score": f["score"],               # store absolute score
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
    push_risk_scores()
    print("Risk scores updated successfully.")
