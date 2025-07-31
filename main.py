from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_executor import Executor
from flask_socketio import SocketIO, emit
import uuid
from threading import Lock

from agent_entry import run_orc_agent
from db import mutual_funds_collection

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

@app.route('/api/mutual_funds', methods=['GET'])
def get_all_mutual_funds():
    mutual_funds = mutual_funds_collection.find()
    mutual_funds_list = []
    for fund in mutual_funds:
        fund["_id"] = str(fund["_id"])
        mutual_funds_list.append(fund)
    return jsonify({"mutual_funds": mutual_funds_list}), 200

@app.route('/sendUserInputs', methods=['POST'])
def send_user_inputs():
    try:
        data = request.get_json()
        user_inputs = {
            "objective": data.get("objective", {}).get("currentKey", ""),
            "risk": data.get("risk", {}).get("currentKey", ""),
            "investment_horizon": data.get("yearsToAchieve", ""),
            "monthly_investment": data.get("monthlyInvestment", 1000),
            "age": data.get("age", 0),
        }
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Store initial status
        with store_lock:
            response_store[task_id] = {
                "status": "processing",
                "result": None,
                "error": None
            }

        # Submit async task
        future = executor.submit(run_orc_agent_with_callback, user_inputs, task_id)
        
        return jsonify({
            "status": "processing", 
            "task_id": task_id,
            "message": "User inputs are being processed"
        }), 202

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def run_orc_agent_with_callback(user_inputs, task_id):
    """Wrapper function to handle the response and store it"""
    try:
        result = run_orc_agent(user_inputs)
        with store_lock:
            response_store[task_id] = {
                "status": "completed",
                "result": result,
                "error": None
            }
        return result
    except Exception as e:
        with store_lock:
            response_store[task_id] = {
                "status": "error",
                "result": None,
                "error": str(e)
            }
        raise

@app.route('/startTask', methods=['POST'])
def start_task():
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
        with store_lock:
            response_store[task_id] = {
                "status": "processing",
                "result": None,
                "error": None
            }

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

@app.route('/getResult/<task_id>', methods=['GET'])
def get_result(task_id):
    """Endpoint to check task status and get result"""
    with store_lock:
        task_data = response_store.get(task_id)
    
    if not task_data:
        return jsonify({"error": "Task not found"}), 404
    
    if task_data["status"] == "processing":
        return jsonify({
            "status": "processing",
            "message": "Task is still being processed"
        }), 202
    elif task_data["status"] == "completed":
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

if __name__ == "__main__":
    socketio.run(app, debug=True, port=5000)
