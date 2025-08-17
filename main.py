from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_executor import Executor
from flask_socketio import SocketIO, emit
import uuid
from threading import Lock
import os
from agent_entry import run_orc_agent
from db import mutual_funds_collection, report_collection, stratergy_collection
import redis
import json
import pickle
import re
import unicodedata

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={
    r"/*": {
        "origins": [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "https://money-fi-frontend.vercel.app"
        ]
    }
})

# Initialize Flask-Executor
executor = Executor(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize response store
response_store = {}
store_lock = Lock()

# Use environment variable for Redis URL in production, fallback to localhost for dev
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL)

@app.route('/api/mutual_funds', methods=['GET'])
def get_all_mutual_funds():
    mutual_funds = mutual_funds_collection.find()
    mutual_funds_list = []
    for fund in mutual_funds:
        fund["_id"] = str(fund["_id"])
        mutual_funds_list.append(fund)
    return jsonify({"mutual_funds": mutual_funds_list}), 200

def run_orc_agent_with_callback(user_inputs, task_id):
    try:
        result = run_orc_agent(user_inputs)
        set_response_store(task_id, {
            "status": "completed",
            "result": result,
            "error": None
        })
        return result
    except Exception as e:
        set_response_store(task_id, {
            "status": "error",
            "result": None,
            "error": str(e)
        })
        raise

@app.route('/startTask', methods=['POST'])
def start_task():
    try:
        data = request.get_json()
        user_inputs = data.get("user_inputs", {})
        
        # Parse user inputs
        parsed_inputs = {
            "objective": user_inputs.get("objective", {}).get("currentKey", ""),
            "risk": "Moderate",
            "investment_horizon": user_inputs.get("yearsToAchieve", ""),
            "monthly_investment": 0,
            "age": user_inputs.get("age", 0),
            "mutual_fund": 3000,
            "etf": 2000,
            "bond": 1000
        }
        print("📤 Parsed user inputs:", parsed_inputs)

        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Store initial status
        set_response_store(task_id, {
            "status": "processing",
            "result": None,
            "error": None
        })
        # Submit async task
        future = executor.submit(run_orc_agent_with_callback, parsed_inputs, task_id)
        
        return jsonify({
            "status": "processing", 
            "task_id": task_id,
            "message": "User inputs are being processed"
        }), 202

    except Exception as e:
        print("❌ Error in /startTask:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/getReportByType', methods=['POST'])
def get_report_by_type():
    try:
        data = request.get_json(force=True) or {}
        strategy_type = data.get("type")
        computed_allocation = data.get("computedAllocation", {}) or {}

        if strategy_type is None:
            return jsonify({"error": "Missing 'type' in request body"}), 400

        strategy_type = int(strategy_type)
        report = report_collection.find_one({"type": strategy_type})
        if not report:
            return jsonify({"error": "No report found for the given type."}), 404

        # --- helpers ---------------------------------------------------------
        def _num(v):
            try:
                n = float(v)
                return int(n) if n.is_integer() else n
            except Exception:
                return 0

        def _normalize_key(k: str) -> str:
            k = (k or "").replace("_", " ").replace("-", " ").strip()
            norm = k.lower().replace(" ", "")
            mapping = {
                "mutualfund": "Mutual Funds",
                "mutualfunds": "Mutual Funds",
                "mf": "Mutual Funds",
                "etf": "ETFs",
                "etfs": "ETFs",
                "bond": "Bonds",
                "bonds": "Bonds",
                "sgb": "SGBs",
                "sgbs": "SGBs",
                "sovereigngoldbonds": "SGBs",
            }
            return mapping.get(norm, k if k else "Unknown")

        def _clean_amounts(d: dict | None) -> dict:
            if not isinstance(d, dict):
                return {}
            out = {}
            for key, val in d.items():
                if not isinstance(key, str):
                    continue
                # skip percentages and totals
                kl = key.lower()
                if key.endswith("%") or kl in ("totalmonthly", "totallumpsum"):
                    continue
                if isinstance(val, dict) or isinstance(val, list):
                    continue
                out[_normalize_key(key)] = _num(val)
            return out
        # ---------------------------------------------------------------------

        # Accept either new or legacy shapes from the client
        lump_in = (
            computed_allocation.get("lumpsumAmounts")
            or computed_allocation.get("lumpsum")
            or computed_allocation.get("lumpsum_allocations")
            or {}
        )
        mon_in = (
            computed_allocation.get("monthlyAmounts")
            or computed_allocation.get("monthly")
            or computed_allocation.get("monthly_allocations")
            or {}
        )

        lump_clean = _clean_amounts(lump_in)
        mon_clean = _clean_amounts(mon_in)

        # Only update what we actually received
        if lump_clean:
            report["lumpsum_allocations"] = lump_clean
            print(f"✅ Updated lumpsum_allocations for type {strategy_type}: {lump_clean}")

        if mon_clean:
            report["monthly_allocations"] = mon_clean
            print(f"✅ Updated monthly_allocations for type {strategy_type}: {mon_clean}")

        # (optional) derive totals if you want them in the payload
        report["total_lumpsum"] = sum(report.get("lumpsum_allocations", {}).values())
        report["total_monthly"] = sum(report.get("monthly_allocations", {}).values())

        report["_id"] = str(report["_id"])
        return jsonify({"report": report}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
def extract_investment_data(agent_text: str, name: str, type: int) -> dict:
    result = {
        "type": type,
        "name": name,
        "monthly_allocations": {},
        "lumpsum_allocations": {},
        "monthly_mutual_funds": [],
        "lumpsum_mutual_funds": [],
        "monthly_etfs": [],
        "lumpsum_etfs": [],
        "monthly_bonds": [],
        "lumpsum_bonds": [],
        "monthly_sgbs": [],
        "lumpsum_sgbs": []
    }

    # 1) Clean markdown-style code block wrapper (```json ... ```)
    agent_text = agent_text.strip()

    if not agent_text:
        print(f"⚠️ agent_text is empty for type {type}")
        return result

    if agent_text.startswith("```"):
        agent_text = re.sub(r"^```(?:json)?\s*", "", agent_text, flags=re.IGNORECASE)
        agent_text = re.sub(r"```$", "", agent_text.strip())

    # 2) Parse JSON
    try:
        payload = json.loads(agent_text)
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error for type {type}: {e}")
        print(f"🚨 Raw agent_text (first 300 chars):\n{repr(agent_text[:300])}")
        return result

    # 3) Extract data
    rec = payload.get("Investment Portfolio Recommendation", {})

    # Monthly Investment
    monthly = rec.get("Monthly Investment", {})
    result["monthly_allocations"] = monthly.get("Allocation", {})

    for mf in monthly.get("Mutual Funds Details", []):
        result["monthly_mutual_funds"].append({
            "name": mf.get("Fund Name"),
            "category": mf.get("Category"),
            "return_5y": mf.get("5-Year Return"),
            "expense_ratio": mf.get("Expense Ratio"),
            "key_metrics": mf.get("Key Metrics")
        })

    for etf in monthly.get("ETFs Details", []):
        result["monthly_etfs"].append({
            "name": etf.get("ETF Name"),
            "return_3y": etf.get("3-Year Return"),
            "expense_ratio": etf.get("Expense Ratio"),
            "standard_deviation": etf.get("Standard Deviation"),
            "key_metrics": etf.get("Key Metrics")
        })

    for bond in monthly.get("Bonds Details", []):
        result["monthly_bonds"].append({
            "name": bond.get("Bond Name"),
            "ytm": bond.get("YTM"),
            "coupon_rate": bond.get("Coupon Rate"),
            "maturity_date": bond.get("Maturity Date"),
            "last_traded_price": bond.get("Last Traded Price"),
            "key_metrics": bond.get("Key Metrics")
        })

    for sgb in monthly.get("SGBs Details", []):
        result["monthly_sgbs"].append({
            "name": sgb.get("Bond Name"),
            "last_traded_price": sgb.get("Last Traded Price (LTP)"),
            "interest_rate": sgb.get("Interest Rate"),
            "maturity_date": sgb.get("Maturity Date"),
            "expected_returns": sgb.get("Expected Returns")
        })

    # Lumpsum Investment
    lumpsum = rec.get("Lumpsum Investment", {})
    result["lumpsum_allocations"] = lumpsum.get("Allocation", {})

    for mf in lumpsum.get("Mutual Funds Details", []):
        result["lumpsum_mutual_funds"].append({
            "name": mf.get("Fund Name"),
            "category": mf.get("Category"),
            "return_5y": mf.get("5-Year Return"),
            "expense_ratio": mf.get("Expense Ratio"),
            "key_metrics": mf.get("Key Metrics")
        })

    for etf in lumpsum.get("ETFs Details", []):
        result["lumpsum_etfs"].append({
            "name": etf.get("ETF Name"),
            "return_3y": etf.get("3-Year Return"),
            "expense_ratio": etf.get("Expense Ratio"),
            "standard_deviation": etf.get("Standard Deviation"),
            "key_metrics": etf.get("Key Metrics")
        })

    for bond in lumpsum.get("Bonds Details", []):
        result["lumpsum_bonds"].append({
            "name": bond.get("Bond Name"),
            "ytm": bond.get("YTM"),
            "coupon_rate": bond.get("Coupon Rate"),
            "maturity_date": bond.get("Maturity Date"),
            "last_traded_price": bond.get("Last Traded Price"),
            "key_metrics": bond.get("Key Metrics")
        })

    for sgb in lumpsum.get("SGBs Details", []):
        result["lumpsum_sgbs"].append({
            "name": sgb.get("Bond Name"),
            "last_traded_price": sgb.get("Last Traded Price (LTP)"),
            "interest_rate": sgb.get("Interest Rate"),
            "maturity_date": sgb.get("Maturity Date"),
            "expected_returns": sgb.get("Expected Returns")
        })

    # 4) Save to MongoDB (if MongoDB collection is defined)
    print("📊 Extracted investment data:", result)
    try:
        report_collection.find_one_and_delete({"type": type})
        report_collection.insert_one(result)
        print(f"✅ Investment data for type {type} saved to MongoDB")
    except Exception as e:
        print(f"❌ Error saving to MongoDB for type {type}: {e}")

    return result

@app.route('/getTaskResult/<task_id>', methods=['GET'])
def get_task_result(task_id):
    results = result_collection.find_one({"task_id": task_id})
    if results:
        results["_id"] = str(results["_id"])
        return jsonify(results), 200
    else:
        return jsonify({"error": "Task not found"}), 404

@app.route('/getResult/<task_id>', methods=['GET'])
def get_result(task_id):
    """Endpoint to check task status and get result"""
    task_data = get_response_store(task_id)
    
    if not task_data:
        return jsonify({"error": "Task not found"}), 404
    
    if task_data["status"] == "processing":
        return jsonify({
            "status": "processing",
            "message": "Task is still being processed"
        }), 202
    elif task_data["status"] == "completed":
        result = extract_investment_data(task_data["result"], task_id)
        return jsonify({
            "status": "completed",
            "result": result
        }), 200
    elif task_data["status"] == "error":
        return jsonify({
            "status": "error",
            "error": task_data["error"]
        }), 500

@app.route('/addStratergy', methods=['POST'])
def add_stratergies():
    try:
        data = request.get_json()
        if not data or "strategies" not in data:
            return jsonify({"error": "Missing 'strategies' in request body"}), 400

        result = stratergy_collection.insert_one(data)
        return jsonify({
            "message": "Strategies added successfully",
            "inserted_id": str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

import re
from typing import Tuple

def _parse_expected_return(text: str | None, years_fallback: float) -> Tuple[float, float]:
    """
    Returns (annual_rate_float, years_used).
    If 'total' is present, converts total return over T years to annualised (CAGR).
    Otherwise treats % as annual rate.
    """
    if not text:
        return 0.0, float(years_fallback or 0.0)

    s = re.sub(r"\s+", " ", (text or "").strip().lower())

    # pick %; if a range like "10-12%" take the midpoint
    nums = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*%", s)]
    if not nums:
        pct = 0.0
    elif len(nums) == 1:
        pct = nums[0]
    else:
        pct = (min(nums) + max(nums)) / 2.0
    pct /= 100.0

    # years (fallback if not present)
    y = re.search(r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?|yr|y)", s)
    years = float(y.group(1)) if y else float(years_fallback or 0.0)

    # detect modes
    is_per_annum = any(k in s for k in ("p.a", "per annum", "pa", "cagr", "annualised", "annualized"))
    is_total = ("total" in s or "cumulative" in s or "overall" in s) and not is_per_annum

    if is_total and years > 0:
        annual = (1.0 + pct) ** (1.0 / years) - 1.0
    else:
        annual = pct

    return float(annual), float(years)

def _monthly_rate(annual_rate: float) -> float:
    """Convert effective annual rate to equivalent monthly rate."""
    return (1.0 + float(annual_rate)) ** (1.0 / 12.0) - 1.0

def _fv_sip(monthly: float, annual_rate: float, years: float, *, annuity_due: bool = False) -> float:
    """Future value of a monthly SIP with monthly compounding."""
    n = int(round(12 * max(years, 0)))
    if n <= 0 or monthly <= 0:
        return 0.0
    r_m = _monthly_rate(annual_rate)
    if abs(r_m) < 1e-12:
        fv = monthly * n
    else:
        fv = monthly * (((1 + r_m) ** n - 1) / r_m)
    return fv * (1 + r_m if annuity_due else 1.0)  # set annuity_due=True if you truly invest at start of month

def _fv_lumpsum(amount: float, annual_rate: float, years: float) -> float:
    """Future value of a lumpsum using the SAME monthly comp convention."""
    n = int(round(12 * max(years, 0)))
    if n <= 0 or amount <= 0:
        return float(amount)
    r_m = _monthly_rate(annual_rate)
    return float(amount) * (1 + r_m) ** n

def _compute_amounts_from_percentages(time: float, money: int, lumpsum: int, alloc: dict, expectedReturn: str) -> dict:
    """Compute MF/ETF/Bond rupee amounts from percentage fields in `alloc`,
    and compute maturity amounts from time, money, lumpsum, and expectedReturn."""
    monthly_alloc = alloc.get("monthly", {}) or {}
    lumpsum_alloc = alloc.get("lumpsum", {}) or {}

    # monthly amounts
    amt_mf_monthly  = int(round(money * (monthly_alloc.get("MutualFunds%", 0) / 100.0)))
    amt_etf_monthly = int(round(money * (monthly_alloc.get("ETFs%",        0) / 100.0)))
    amt_bond_monthly= int(round(money * (monthly_alloc.get("Bonds%",       0) / 100.0)))
    amt_sgb_monthly = int(round(money * (monthly_alloc.get("SGBs%",        0) / 100.0)))

    # lumpsum amounts
    amt_mf_lumpsum  = int(round(lumpsum * (lumpsum_alloc.get("MutualFunds%", 0) / 100.0)))
    amt_etf_lumpsum = int(round(lumpsum * (lumpsum_alloc.get("ETFs%",        0) / 100.0)))
    amt_bond_lumpsum= int(round(lumpsum * (lumpsum_alloc.get("Bonds%",       0) / 100.0)))
    amt_sgb_lumpsum = int(round(lumpsum * (lumpsum_alloc.get("SGBs%",        0) / 100.0)))

    # returns / FV
    annual_rate, years = _parse_expected_return(expectedReturn, time)

    total_invested_monthly = int(round(max(money, 0) * 12 * max(years, 0)))
    total_invested_lumpsum = int(round(max(lumpsum, 0)))
    total_invested = total_invested_monthly + total_invested_lumpsum

    # SIP assumed end-of-month; set annuity_due=True if you want start-of-month
    fv_monthly = _fv_sip(float(money), float(annual_rate), float(years), annuity_due=False)
    fv_lumpsum = _fv_lumpsum(float(lumpsum), float(annual_rate), float(years))
    maturity_total = fv_monthly + fv_lumpsum
    returns_amt = maturity_total - total_invested

    return {
        "monthlyAmounts": {
            "Mutual Funds": amt_mf_monthly,
            "ETFs": amt_etf_monthly,
            "Bonds": amt_bond_monthly,
            "SGBs": amt_sgb_monthly,
        },
        "lumpsumAmounts": {
            "Mutual Funds": amt_mf_lumpsum,
            "ETFs": amt_etf_lumpsum,
            "Bonds": amt_bond_lumpsum,
            "SGBs": amt_sgb_lumpsum,
        },
        "monthlyPercentages": monthly_alloc,
        "lumpsumPercentages": lumpsum_alloc,
        "maturity": {
            "TotalInvested": int(round(total_invested)),
            "Returns": int(round(returns_amt)),
            "MaturityAmount": int(round(maturity_total)),
            "monthly_FV": int(round(fv_monthly)),
            "lumpsum_FV": int(round(fv_lumpsum)),
            "annualRateUsed": float(annual_rate),
            "yearsUsed": float(years),
        },
    }

@app.route('/getStratergy', methods=['POST'])
def get_strategy():
    try:
        data = request.get_json() or {}
        print("🔍 Strategy request data:", data)

        time = data.get("yearsToAchieve")
        money = data.get("monthlyInvestment")
        lumpsum = data.get("lumpsumInvestment")

        # Basic validation
        if time is None or money is None or lumpsum is None:
            return jsonify({"error": "yearsToAchieve, monthlyInvestment, and lumpsumInvestment are required"}), 400
        try:
            time = float(time)
            money = int(money)
            lumpsum = int(lumpsum)
        except Exception:
            return jsonify({"error": "Invalid types for yearsToAchieve, monthlyInvestment, or lumpsumInvestment"}), 400

        # Determine category (same logic as before)
        category = None
        if 100 <= money < 500:
            if 1 <= time < 3:
                category = 11
            elif 3 <= time < 6:
                category = 12
            elif time >= 6:
                category = 13
        elif 500 <= money < 10500:
            if 1 <= time < 3:
                category = 21
            elif 3 <= time < 6:
                category = 22
            elif time >= 6:
                category = 23
        elif money >= 10500:
            if 1 <= time < 3:
                category = 31
            elif 3 <= time < 6:
                category = 32
            elif time >= 6:
                category = 33

        if 1000 <= lumpsum < 10500:
            category = category * 10 + 1
        elif lumpsum >= 10500:
            category = category * 10 + 2

        if category is None:
            return jsonify({"message": "No matching category for the given inputs."}), 400

        # Fetch matching strategy docs
        docs = list(stratergy_collection.find({"type": category}))
        if not docs:
            return jsonify({"message": "No strategies found for the given criteria."}), 404

        # Build response: for each strategy in each doc, compute rupee allocations from %
        out_strategies = []
        for doc in docs:
            for s in (doc.get("strategies") or []):
                alloc = s.get("allocation") or {}
                expectedReturn = s.get("expectedReturn")
                computed = _compute_amounts_from_percentages(time, money, lumpsum, alloc, expectedReturn)
                out_strategies.append({
                    "name": s.get("name"),
                    "description": s.get("description"),
                    "riskLevel": s.get("riskLevel"),
                    "expectedReturn": s.get("expectedReturn"),
                    "maturityAmount": computed["maturity"],  
                    "templateAllocation": alloc,                 # original template from DB
                    "computedAllocation": {                      # final monthly and lumpsum split in ₹
                        "monthlyAmounts": computed["monthlyAmounts"],
                        "lumpsumAmounts": computed["lumpsumAmounts"],
                        "totalMonthly": money,
                        "totalLumpsum": lumpsum
                    },
                    "type": doc.get("type")
                })

        return jsonify({"strategy": out_strategies}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def set_response_store(task_id, data):
    redis_client.set(f"response_store:{task_id}", pickle.dumps(data), ex=3600)  # 1 hour expiry

def get_response_store(task_id):
    data = redis_client.get(f"response_store:{task_id}")
    if data:
        return pickle.loads(data)
    return None

if __name__ == "__main__":
    socketio.run(app, debug=True, port=5000)
