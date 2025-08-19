from main import extract_investment_data
from agent_entry import run_orc_agent
from stratergist.main import run_strategist_agent
from db import stratergy_collection

user_inputs = {
    "lumpsum": 15000,
    "investment_horizon": "5 years",
    "monthly_investment": 100
}

# Run the strategist agent to generate strategy data
stratergy_data = run_strategist_agent(user_inputs)

# Add a base type key to the strategy data
base_type_id = 122
formatted_data = {
    "type": base_type_id,
    "strategies": stratergy_data["strategies"]
}

# Insert the formatted strategy data into the database
try:
    stratergy_collection.delete_many({"type": base_type_id})  # Clear existing strategies with the same type_id
    result = stratergy_collection.insert_one(formatted_data)
    print(f"✅ Strategy added successfully with ID: {result.inserted_id}")
except Exception as e:
    print(f"❌ Error adding strategy: {e}")

# Loop through strategies and run ORC agent
for index, strategy in enumerate(formatted_data["strategies"], start=1):
    # Calculate type_id for the current strategy
    strategy_type_id = int(f"{base_type_id}{index}")  # Append index to base type_id

    # Extract allocation percentages
    monthly_allocation = strategy["allocation"]["monthly"]
    lumpsum_allocation = strategy["allocation"]["lumpsum"]

    # Prepare user inputs for ORC agent
    user_inputs_for_orc = {
        "objective": strategy["name"],  # Use strategy name as objective
        "investment_horizon": user_inputs["investment_horizon"],  # Example horizon
        "age": 22,  # Example age
        "mutual_fund": monthly_allocation.get("MutualFunds%", 0) * user_inputs["monthly_investment"] // 100,
        "mutual_fund_lumpsum": lumpsum_allocation.get("MutualFunds%", 0) * user_inputs["lumpsum"] // 100,
        "etf": monthly_allocation.get("ETFs%", 0) * user_inputs["monthly_investment"] // 100,
        "etf_lumpsum": lumpsum_allocation.get("ETFs%", 0) * user_inputs["lumpsum"] // 100,
        "bond": monthly_allocation.get("Bonds%", 0) * user_inputs["monthly_investment"] // 100,
        "bond_lumpsum": lumpsum_allocation.get("Bonds%", 0) * user_inputs["lumpsum"] // 100,
        "sgb": monthly_allocation.get("SGBs%", 0) * user_inputs["monthly_investment"] // 100,
        "sgb_lumpsum": lumpsum_allocation.get("SGBs%", 0) * user_inputs["lumpsum"] // 100,
        "risk": strategy["riskLevel"]  # Use risk level from strategy
    }
    print(user_inputs_for_orc)
    # Run ORC agent
    try:
        orc_result = run_orc_agent(user_inputs_for_orc)
        extract_investment_data(orc_result, strategy["name"], strategy_type_id)
    except Exception as e:
        print(f"❌ Error running ORC agent for strategy '{strategy['name']}' with type_id {strategy_type_id}: {e}")