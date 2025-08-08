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
    
@app.route('/getReportByType/<type>', methods=['GET'])
def get_report_by_type(type):
    try:
        if type is None:
            return jsonify({"error": "Missing 'type' in request body"}), 400
        type = int(type)
        report = report_collection.find_one({"type": type})
        if not report:
            return jsonify({"error": "No report found for the given type."}), 404

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

@app.route('/getStratergy', methods=['POST'])
def get_strategy():
    try:
        data = request.get_json()
        print("🔍 Strategy request data:", data)
        time = data.get("yearsToAchieve")
        money = data.get("monthlyInvestment")

        if money >= 100 and money < 500:
            if time >= 1 and time < 3:
                category = 11
            elif time >= 3 and time < 6:
                category = 12
            elif time >= 6:
                category = 13
        elif money >= 500 and money < 10000:
            if time >= 1 and time < 3:
                category = 21
            elif time >= 3 and time < 6:
                category = 22
            elif time >= 6:
                category = 23
        elif money >= 10000:
            if time >= 1 and time < 3:
                category = 31
            elif time >= 3 and time < 6:
                category = 32
            elif time >= 6:
                category = 33

        # Fetch matching strategies
        stratergies = list(stratergy_collection.find({"type": category}))
        for s in stratergies:
            s["_id"] = str(s["_id"])

        if not stratergies:
            return jsonify({"message": "No strategies found for the given criteria."}), 404

        return jsonify({"strategy": stratergies}), 200

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
#     agent_text = """
#     ```json
# {
#   "Investment Portfolio Recommendation": {
#     "Monthly Investment Allocation": {
#       "Mutual Funds": 8400,
#       "ETFs": 3000,
#       "Bonds": 600
#     },
#     "Mutual Funds Details": [
#       {
#         "Fund Name": "Axis Small Cap Fund - Direct Plan",
#         "Category": "Equity - Small Cap",
#         "5-Year Return": 31.29,
#         "Expense Ratio": 0.56,
#         "Key Metrics": {
#           "Sharpe Ratio": "N/A",
#           "Standard Deviation": 14.22,
#           "Minimum Investment": 100,
#           "Peer Comparison": "Top 10% over 3 and 5 years"
#         }
#       },
#       {
#         "Fund Name": "Bandhan Small Cap Fund - Direct Plan",
#         "Category": "Equity - Small Cap",
#         "5-Year Return": 37.11,
#         "Expense Ratio": 0.39,
#         "Key Metrics": {
#           "Sharpe Ratio": "N/A",
#           "Standard Deviation": 17.83,
#           "Minimum Investment": 1000,
#           "Peer Comparison": "Top 5% over 3 years"
#         }
#       },
#       {
#         "Fund Name": "HDFC Flexi Cap Fund - Direct Plan",
#         "Category": "Equity - Flexi Cap",
#         "5-Year Return": 29.18,
#         "Expense Ratio": 0.72,
#         "Key Metrics": {
#           "Sharpe Ratio": "N/A",
#           "Standard Deviation": 11.92,
#           "Minimum Investment": 100,
#           "Peer Comparison": "Top 15% over 5 years"
#         }
#       },
#       {
#         "Fund Name": "Edelweiss Mid Cap Fund - Direct Plan",
#         "Category": "Equity - Mid Cap",
#         "5-Year Return": 33.19,
#         "Expense Ratio": 0.39,
#         "Key Metrics": {
#           "Sharpe Ratio": "N/A",
#           "Standard Deviation": 16.19,
#           "Minimum Investment": 100,
#           "Peer Comparison": "Top 10% over 3 years"
#         }
#       },
#       {
#         "Fund Name": "Motilal Oswal Midcap Fund - Direct Plan",
#         "Category": "Equity - Mid Cap",
#         "5-Year Return": 36.21,
#         "Expense Ratio": 0.68,
#         "Key Metrics": {
#           "Sharpe Ratio": "N/A",
#           "Standard Deviation": 17.94,
#           "Minimum Investment": 500,
#           "Peer Comparison": "Top 5% over 5 years"
#         }
#       }
#     ],
#     "ETFs Details": [
#       {
#         "ETF Name": "Motilal Oswal NASDAQ 100 ETF",
#         "3-Year Return": 26.61,
#         "Expense Ratio": 0.58,
#         "Standard Deviation": 17.44,
#         "Key Metrics": {
#           "1Y Return": 27.69,
#           "Sharpe Ratio": "N/A",
#           "Peer Comparison": "Top 15% for 1Y and 3Y"
#         }
#       },
#       {
#         "ETF Name": "Invesco India - Invesco EQQQ NASDAQ-100 ETF FoF - Direct Plan",
#         "3-Year Return": 26.81,
#         "Expense Ratio": 0.16,
#         "Standard Deviation": "N/A",
#         "Key Metrics": {
#           "1Y Return": 26.28,
#           "Sortino Ratio": 2.0,
#           "Peer Comparison": "Top tier performance"
#         }
#       },
#       {
#         "ETF Name": "Aditya Birla Sun Life Nifty Healthcare ETF",
#         "3-Year Return": 24.62,
#         "Expense Ratio": 0.19,
#         "Standard Deviation": "N/A",
#         "Key Metrics": {
#           "1Y Return": 11.83,
#           "Sortino Ratio": 1.78,
#           "Peer Comparison": "Ranks well in healthcare sector"
#         }
#       },
#       {
#         "ETF Name": "ICICI Prudential Nifty Healthcare ETF",
#         "3-Year Return": 24.43,
#         "Expense Ratio": 0.15,
#         "Standard Deviation": "N/A",
#         "Key Metrics": {
#           "1Y Return": 11.93,
#           "Sortino Ratio": 1.76,
#           "Peer Comparison": "Competitive in healthcare sector"
#         }
#       },
#       {
#         "ETF Name": "Aditya Birla Sun Life Silver ETF",
#         "3-Year Return": 27.05,
#         "Expense Ratio": 0.35,
#         "Standard Deviation": "N/A",
#         "Key Metrics": {
#           "1Y Return": 38.71,
#           "Sortino Ratio": 1.74,
#           "Peer Comparison": "Ranks highly among silver ETFs"
#         }
#       }
#     ],
#     "Bonds Details": [
#       {
#         "Bond Name": "82HUDCO27",
#         "YTM": 3.58,
#         "Coupon Rate": 8.2,
#         "Maturity Date": "2027-03-05",
#         "Additional Details": {
#           "Type": "Corporate Bond",
#           "Price vs Face Value": "₹72.00 (Premium)"
#         }
#       },
#       {
#         "Bond Name": "824GS2027",
#         "YTM": 5.06,
#         "Coupon Rate": 8.24,
#         "Maturity Date": "2027-12-31",
#         "Additional Details": {
#           "Type": "Government Security (G-Sec)",
#           "Price vs Face Value": "₹7.27 (Premium)"
#         }
#       },
#       {
#         "Bond Name": "738GS2027",
#         "YTM": 5.71,
#         "Coupon Rate": 7.38,
#         "Maturity Date": "2027-12-31",
#         "Additional Details": {
#           "Type": "Government Security (G-Sec)",
#           "Price vs Face Value": "₹3.79 (Premium)"
#         }
#       },
#       {
#         "Bond Name": "850NHAI29",
#         "YTM": 4.75,
#         "Coupon Rate": 8.5,
#         "Maturity Date": "2029-02-05",
#         "Additional Details": {
#           "Type": "Corporate Bond",
#           "Price vs Face Value": "₹122.01 (Premium)"
#         }
#       },
#       {
#         "Bond Name": "709GS2054",
#         "YTM": 7.02,
#         "Coupon Rate": 7.09,
#         "Maturity Date": "2054-12-31",
#         "Additional Details": {
#           "Type": "Government Security (G-Sec)",
#           "Price vs Face Value": "₹1.22 (Premium)"
#         }
#       }
#     ]
#   }
# }
# ```
#     """
#     extract_investment_data(agent_text, 323)
