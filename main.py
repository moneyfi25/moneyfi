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
        data = request.get_json()
        type = data.get("type")
        computed_allocation = data.get("computedAllocation", {})
        
        if type is None:
            return jsonify({"error": "Missing 'type' in request body"}), 400
        
        type = int(type)
        report = report_collection.find_one({"type": type})
        
        if not report:
            return jsonify({"error": "No report found for the given type."}), 404

        # Update allocations if computedAllocation is provided
        if computed_allocation:
            # Extract only the allocation amounts (not percentages or totalMonthly)
            new_allocations = {}
            for key, value in computed_allocation.items():
                if not key.endswith("%") and key != "totalMonthly":
                    new_allocations[key] = value
            
            # Update the report's allocations
            if new_allocations:
                report["allocations"] = new_allocations
                print(f"✅ Updated allocations for type {type}: {new_allocations}")

        report["_id"] = str(report["_id"])
        return jsonify({"report": report}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def extract_investment_data(agent_text: str, type: int) -> dict:
    result = {
        "type": type,
        "allocations": {},
        "mutual_funds": [],
        "etfs": [],
        "bonds": []
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
    result["allocations"] = rec.get("Monthly Investment Allocation", {})

    # Mutual Funds
    for mf in rec.get("Mutual Funds Details", []):
        result["mutual_funds"].append({
            "name": mf.get("Fund Name"),
            "category": mf.get("Category"),
            "return_5y": mf.get("5-Year Return"),
            "expense_ratio": mf.get("Expense Ratio"),
            "key_metrics": mf.get("Key Metrics")
        })

    # ETFs
    for etf in rec.get("ETFs Details", []):
        result["etfs"].append({
            "name": etf.get("ETF Name"),
            "return_3y": etf.get("3-Year Return"),
            "expense_ratio": etf.get("Expense Ratio"),
            "standard_deviation": etf.get("Standard Deviation"),
            "key_metrics": etf.get("Key Metrics")
        })

    # Bonds
    for bond in rec.get("Bonds Details", []):
        result["bonds"].append({
            "name": bond.get("Bond Name"),
            "ytm": bond.get("YTM"),
            "coupon_rate": bond.get("Coupon Rate"),
            "maturity_date": bond.get("Maturity Date"),
            "additional_details": bond.get("Additional Details")
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

        # Insert the whole strategies object as one document
        result = stratergy_collection.insert_one(data)
        return jsonify({
            "message": "Strategies added successfully",
            "inserted_id": str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def _compute_amounts_from_percentages(money: int, alloc: dict):
    """Compute MF/ETF/Bond rupee amounts from percentage fields in `alloc`."""
    # Read percents (accept a few possible key styles)
    p_mf   = alloc.get("Mutual Funds%", alloc.get("MutualFunds%", alloc.get("MF%", 0))) or 0
    p_etf  = alloc.get("ETFs%",        alloc.get("ETF%",        0)) or 0
    p_bond = alloc.get("Bonds%",       alloc.get("Bond%",       0)) or 0

    total_pct = (p_mf or 0) + (p_etf or 0) + (p_bond or 0)

    # If no % provided, try to infer from absolute fields; else fall back to MF=100%
    if not total_pct:
        abs_mf   = alloc.get("Mutual Funds", 0) or 0
        abs_etf  = alloc.get("ETFs", 0) or 0
        abs_bond = alloc.get("Bonds", 0) or 0
        total_abs = abs_mf + abs_etf + abs_bond
        if total_abs > 0:
            p_mf   = round(100 * abs_mf   / total_abs, 2)
            p_etf  = round(100 * abs_etf  / total_abs, 2)
            p_bond = round(100 * abs_bond / total_abs, 2)
            total_pct = p_mf + p_etf + p_bond
        else:
            p_mf, p_etf, p_bond, total_pct = 100, 0, 0, 100  # safe default

    # Normalize if percentages don't sum to 100
    if total_pct != 100 and total_pct > 0:
        scale = 100.0 / total_pct
        p_mf, p_etf, p_bond = p_mf * scale, p_etf * scale, p_bond * scale

    # Compute integer rupee amounts with remainder correction to ensure exact sum
    amt_mf   = int(round(money * (p_mf / 100.0)))
    amt_etf  = int(round(money * (p_etf / 100.0)))
    amt_bond = int(round(money * (p_bond / 100.0)))

    # Fix rounding drift so amounts add up to `money`
    diff = money - (amt_mf + amt_etf + amt_bond)
    if diff != 0:
        # Assign remainder to the bucket with the largest percentage
        triples = [("Mutual Funds", p_mf), ("ETFs", p_etf), ("Bonds", p_bond)]
        triples.sort(key=lambda x: x[1], reverse=True)
        top = triples[0][0]
        if top == "Mutual Funds":
            amt_mf += diff
        elif top == "ETFs":
            amt_etf += diff
        else:
            amt_bond += diff

    print(amt_mf)
    return {
        "amounts": {
            "Mutual Funds": amt_mf,
            "ETFs": amt_etf,
            "Bonds": amt_bond
        },
        "percentages": {
            "Mutual Funds%": round(p_mf, 2),
            "ETFs%": round(p_etf, 2),
            "Bonds%": round(p_bond, 2)
        }
    }

@app.route('/getStratergy', methods=['POST'])
def get_strategy():
    try:
        data = request.get_json() or {}
        print("🔍 Strategy request data:", data)

        time = data.get("yearsToAchieve")
        money = data.get("monthlyInvestment")

        # Basic validation
        if time is None or money is None:
            return jsonify({"error": "yearsToAchieve and monthlyInvestment are required"}), 400
        try:
            time = float(time)
            money = int(money)
        except Exception:
            return jsonify({"error": "Invalid types for yearsToAchieve or monthlyInvestment"}), 400

        # Determine category (same logic as before)
        category = None
        if 100 <= money < 500:
            if 1 <= time < 3:
                category = 11
            elif 3 <= time < 6:
                category = 12
            elif time >= 6:
                category = 13
        elif 500 <= money < 10000:
            if 1 <= time < 3:
                category = 21
            elif 3 <= time < 6:
                category = 22
            elif time >= 6:
                category = 23
        elif money >= 10000:
            if 1 <= time < 3:
                category = 31
            elif 3 <= time < 6:
                category = 32
            elif time >= 6:
                category = 33

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
                computed = _compute_amounts_from_percentages(money, alloc)

                out_strategies.append({
                    "name": s.get("name"),
                    "description": s.get("description"),
                    "riskLevel": s.get("riskLevel"),
                    "expectedReturn": s.get("expectedReturn"),
                    "maturityAmount": s.get("maturityAmount"),
                    "templateAllocation": alloc,                 # original template from DB
                    "computedAllocation": {                      # final monthly split in ₹
                        **computed["amounts"],
                        **computed["percentages"],
                        "totalMonthly": money
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
