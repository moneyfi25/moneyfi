from flask import Flask, request, jsonify
from flask_cors import CORS
from db import mutual_funds_collection
import json

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={
    r"/*": {
        "origins": [
            "http://localhost:5173",
            "http://127.0.0.1:5173"
        ]
    }
})

@app.route('/api/post_mutual_fund', methods=['POST'])
def post_mutual_fund():
    data = request.json

    # build the document
    doc = {
        "name": data["name"].strip(),
        "metrics": {
            "alpha": {
                "investment": float(data["alpha"]["investment"]),
                "category": float(data["alpha"]["category"]),
            },
            "beta": float(data["beta"]),
            "standard_deviation": {
                "investment": float(data["standard_deviation"]["investment"]),
                "category": float(data["standard_deviation"]["category"]),
            },
            "sharpe_ratio": {
                "investment": float(data["sharpe_ratio"]["investment"]),
                "category": float(data["sharpe_ratio"]["category"]),
            },
            "maximum_drawdown": float(data["maximum_drawdown"]),
            "expense_ratio": float(data["expense_ratio"]),
        },
        "returns": {
            "1y": {
                "investment": float(data["returns"]["1y"]["investment"]),
                "category": float(data["returns"]["1y"]["category"]),
            },
            "3y": {
                "investment": float(data["returns"]["3y"]["investment"]),
                "category": float(data["returns"]["3y"]["category"]),
            },
            "5y": {
                "investment": float(data["returns"]["5y"]["investment"]),
                "category": float(data["returns"]["5y"]["category"]),
            }
        },
    }

    # insert into MongoDB
    result = mutual_funds_collection.insert_one(doc)
    return jsonify({
        "status": "success",
        "inserted_id": str(result.inserted_id)
    }), 201

@app.route('/api/mutual_funds', methods=['GET'])
def get_all_mutual_funds():
    mutual_funds = mutual_funds_collection.find()
    mutual_funds_list = []
    for fund in mutual_funds:
        fund["_id"] = str(fund["_id"])
        mutual_funds_list.append(fund)
    return jsonify({"mutual_funds": mutual_funds_list}), 200

@app.route('/api/screener', methods=['POST'])
def screener():
    try:
        data = request.get_json()
        print("🔍 Received data:", data)

        if not all(k in data for k in ('goalAmount', 'monthlyInvestment', 'yearsToAchieve')):
            return jsonify({"error": "Missing required fields"}), 400

        # result = run_screener_agent(data)
        # return jsonify(result), 200 if result["status"] == "success" else 500
        return jsonify({
            "status": "success",
            "message": "Screener functionality is not implemented yet."
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
