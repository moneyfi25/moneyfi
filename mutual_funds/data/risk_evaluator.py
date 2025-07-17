import requests
import statistics
import sys
import os
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
    total_checks = 6

    evaluated = []
    for f in funds:
        s = risk_score(f, expense_med)
        evaluated.append({
            "name": f["name"],
            "score": s,
            # relative_score 0.0 (best) → 1.0 (worst)
            "relative_score": s / total_checks
        })

    # sort by ascending score (lowest-risk first)
    return sorted(evaluated, key=lambda x: x["score"])


if __name__ == "__main__":
    for fund in evaluate_all_risk():
        print(
            f"{fund['name']}: "
            f"score={fund['score']} "
            f"(relative={fund['relative_score']:.2f})"
        )
