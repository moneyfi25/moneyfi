from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_executor import Executor
from flask_socketio import SocketIO, emit
import uuid
from threading import Lock
import subprocess
import os
from agent_entry import run_orc_agent
from db import mutual_funds_collection, result_collection
import redis
import json
import pickle

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={
    r"/*": {
        "origins": [
            "http://localhost:5173",
            "http://127.0.0.1:5173"
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

@app.route('/startTask', methods=['POST', 'OPTIONS'])
def start_task():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    try:
        data = request.get_json()
        user_inputs = data.get("user_inputs", {})
        
        # Parse user inputs
        parsed_inputs = {
            "objective": user_inputs.get("objective", {}).get("currentKey", ""),
            "risk": user_inputs.get("risk", {}).get("currentKey", ""),
            "investment_horizon": user_inputs.get("yearsToAchieve", ""),
            "monthly_investment": user_inputs.get("monthlyInvestment", 1000),
            "age": user_inputs.get("age", 0),
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
import re

def extract_investment_data(agent_text: str, task_id: str) -> dict:
    result = {
        "task_id": task_id,
        "allocations": {},
        "mutual_funds": [],
        "etfs": [],
        "bonds": []
    }

    # 1) Parse the ₹ allocations from the section headers
    for asset in ("Mutual Funds", "ETFs", "Bonds"):
        m = re.search(rf"###\s*{asset}.*?₹([\d,]+)", agent_text)
        if m:
            result["allocations"][asset] = int(m.group(1).replace(",", ""))

    # 2) Mutual Funds: between ### Mutual Funds and ### ETFs
    mf_sec = re.search(r"### Mutual Funds(.*?)(?=### ETFs)", agent_text, re.DOTALL)
    if mf_sec:
        entries = re.split(r"\n\d+\.\s+", mf_sec.group(1))
        for block in entries[1:]:
            name_m = re.match(r"\*\*(.*?)\*\*", block)
            if not name_m:
                continue
            cat_m = re.search(r"\*\*Category:\*\*\s*([^\n]+)", block)
            ret_m = re.search(r"\*\*5-Year Return:\*\*\s*([\d\.]+)%", block)
            exp_m = re.search(r"\*\*Expense Ratio:\*\*\s*([\d\.]+|Not specified)%?", block)

            result["mutual_funds"].append({
                "name":          name_m.group(1).strip(),
                "category":      cat_m.group(1).strip() if cat_m else None,
                "return_5y":     float(ret_m.group(1)) if ret_m else None,
                "expense_ratio": float(exp_m.group(1)) if exp_m and exp_m.group(1) != "Not specified" else None
            })

    # 3) ETFs: between ### ETFs and ### Bonds
    etf_sec = re.search(r"### ETFs(.*?)(?=### Bonds)", agent_text, re.DOTALL)
    if etf_sec:
        entries = re.split(r"\n\d+\.\s+", etf_sec.group(1))
        for block in entries[1:]:
            name_m = re.match(r"\*\*(.*?)\*\*", block)
            if not name_m:
                continue
            ret_m = re.search(r"\*\*3-Year Return:\*\*\s*([\d\.]+)%", block)
            exp_m = re.search(r"\*\*Expense Ratio:\*\*\s*([\d\.]+)%", block)
            std_m = re.search(r"\*\*Standard Deviation:\*\*\s*([\d\.]+)", block)

            result["etfs"].append({
                "name":               name_m.group(1).strip(),
                "return_3y":          float(ret_m.group(1)) if ret_m else None,
                "expense_ratio":      float(exp_m.group(1)) if exp_m else None,
                "standard_deviation": float(std_m.group(1)) if std_m else None
            })

    # 4) Bonds: from ### Bonds up to the next ###-header or end-of-text
    bond_sec = re.search(
        r"### Bonds[^\n]*\n([\s\S]*?)(?=\n###\s*[A-Z]|\Z)",
        agent_text
    )
    if bond_sec:
        entries = re.split(r"\n\d+\.\s+", bond_sec.group(1))
        for block in entries[1:]:
            # Extract bond name from **Bond Name** format
            name_m = re.match(r"\*\*(.*?)\*\*", block)
            ytm_m  = re.search(r"\*\*YTM:\*\*\s*([\d\.]+)%", block)
            coup_m = re.search(r"\*\*Coupon Rate:\*\*\s*([\d\.]+)%", block)
            mat_m  = re.search(r"\*\*Maturity Date:\*\*\s*([^\n]+)", block)

            result["bonds"].append({
                "name":          name_m.group(1).strip() if name_m else None,
                "ytm":           float(ytm_m.group(1))  if ytm_m  else None,
                "coupon_rate":   float(coup_m.group(1)) if coup_m else None,
                "maturity_date": mat_m.group(1).strip()  if mat_m  else None
            })

    # 5) Persist and return
    print("📊 Extracted investment data:", result)
    try:
        result_collection.find_one_and_delete({"task_id": task_id})
        result_collection.insert_one(result)
        print(f"✅ Investment data for task_id {task_id} saved to MongoDB")
    except Exception as e:
        print(f"❌ Error saving to MongoDB for task_id {task_id}: {e}")

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
        extract_investment_data(task_data["result"], task_id)
        return jsonify({
            "status": "completed",
            "result": task_data["result"]
        }), 200
    elif task_data["status"] == "error":
        return jsonify({
            "status": "error",
            "error": task_data["error"]
        }), 500

@app.route('/api/screener', methods=['POST'])
def screener():
    try:
        data = request.get_json()
        print("🔍 Received data:", data)

        if not all(k in data for k in ('goalAmount', 'monthlyInvestment', 'yearsToAchieve')):
            return jsonify({"error": "Missing required fields"}), 400

        return jsonify({
            "status": "success",
            "message": "Screener functionality is not implemented yet."
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def set_response_store(task_id, data):
    # Use pickle for complex objects, or json.dumps for dicts
    redis_client.set(f"response_store:{task_id}", pickle.dumps(data), ex=3600)  # 1 hour expiry

def get_response_store(task_id):
    data = redis_client.get(f"response_store:{task_id}")
    if data:
        return pickle.loads(data)
    return None

if __name__ == "__main__":
    socketio.run(app, debug=True, port=5000)
#     agent_text = """
# Based on your investment profile and objectives, here's a diversified portfolio recommendation for wealth creation over a 5-year horizon with a moderate risk appetite:

# ### Mutual Funds (₹5000 Monthly Investment)
# 1. **Axis Large & Mid Cap Fund - Direct Plan**
#    - **Category:** Equity - Large & Mid Cap
#    - **5-Year Return:** 24.46%
#    - **Expense Ratio:** 0.60%
#    - **Key Metrics:** Sharpe Ratio: 1.76, Standard Deviation: 13.67, Alpha: 4.46

# 2. **Bandhan Large & Mid Cap Fund - Direct Plan**
#    - **Category:** Equity - Large & Mid Cap
#    - **5-Year Return:** 28.38%
#    - **Expense Ratio:** Not specified
#    - **Key Metrics:** Sharpe Ratio: 2.17, Standard Deviation: 13.98, Alpha: 8.58

# 3. **ICICI Prudential Large & Mid Cap Fund - Direct Plan**
#    - **Category:** Equity - Large & Mid Cap
#    - **5-Year Return:** 28.50%
#    - **Expense Ratio:** 0.77%
#    - **Key Metrics:** Sharpe Ratio: 2.37, Standard Deviation: 12.16, Alpha: 7.08

# 4. **HDFC Balanced Advantage Fund - Direct Plan**
#    - **Category:** Hybrid - Dynamic Asset Allocation
#    - **5-Year Return:** 24.39%
#    - **Expense Ratio:** 0.75%
#    - **Key Metrics:** Sharpe Ratio: 2.93, Standard Deviation: 9.42, Alpha: 7.40

# 5. **Nippon India Multi Cap Fund - Direct Plan**
#    - **Category:** Equity - Multi Cap
#    - **5-Year Return:** 32.23%
#    - **Expense Ratio:** Not specified
#    - **Key Metrics:** Sharpe Ratio: 2.15, Standard Deviation: 14.00, Alpha: 6.26

# ### ETFs (₹3000 Monthly Investment)
# 1. **Aditya Birla Sun Life Nifty Healthcare ETF**
#    - **3-Year Return:** 24.62%
#    - **Expense Ratio:** 0.19%
#    - **Standard Deviation:** 16.55

# 2. **Mirae Asset NYSE FANG+ ETF**
#    - **3-Year Return:** 45.19%
#    - **Expense Ratio:** 0.65%
#    - **Standard Deviation:** 25.48

# 3. **Invesco India - Invesco EQQQ NASDAQ-100 ETF FoF - Direct Plan**
#    - **3-Year Return:** 26.81%
#    - **Expense Ratio:** 0.16%
#    - **Standard Deviation:** 18.53

# 4. **Aditya Birla Sun Life Nifty Bank ETF**
#    - **3-Year Return:** 16.21%
#    - **Expense Ratio:** 0.14%
#    - **Standard Deviation:** 14.33

# 5. **Mirae Asset Nifty Financial Services ETF**
#    - **3-Year Return:** 17.73%
#    - **Expense Ratio:** 0.12%
#    - **Standard Deviation:** 13.89

# ### Bonds (₹2000 Monthly Investment)
# 1. **710GS2029 (Government Security)**
#    - **YTM:** 5.63%
#    - **Coupon Rate:** 7.10%
#    - **Maturity Date:** December 31, 2029

# 2. **738GS2027 (Government Security)**
#    - **YTM:** 5.71%
#    - **Coupon Rate:** 7.38%
#    - **Maturity Date:** December 31, 2027

# 3. **82HUDCO27 (Corporate Bond)**
#    - **YTM:** 3.58%
#    - **Coupon Rate:** 8.20%
#    - **Maturity Date:** March 5, 2027

# 4. **79NHIT35 (Corporate Bond)**
#    - **YTM:** 7.17%
#    - **Coupon Rate:** 7.90%
#    - **Maturity Date:** October 24, 2035

# 5. **82IGT31 (Corporate Bond)**
#    - **YTM:** 7.61%
#    - **Coupon Rate:** 8.20%
#    - **Maturity Date:** May 6, 2031

# ### Estimated Returns
# - **Mutual Funds and ETFs:** Expect an average annual return of around 20-25% based on historical performance.
# - **Bonds:** Expect an average annual yield of around 5-7% based on YTM and coupon rates.

# ### Summary
# This portfolio provides a balanced approach to wealth creation, combining growth-oriented mutual funds and ETFs with stable income from bonds. Regularly review and adjust your portfolio based on market conditions and personal financial goals.
# """
#     extract_investment_data(agent_text, "df3484a2-4a13-4db1-9c59-100f7d25627d")
