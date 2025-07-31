from pymongo import MongoClient, UpdateOne
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db import sgb_collection

def premium_evaluator(
    market_gold_price: float = 10000.0,  # per gram 999 purity gold
    premium_threshold: float = 0.03     # 3% premium is safe
):
    """
    Evaluates the premium of each SGB vs 999 gold rate and updates MongoDB with `safe_premium` flag.
    
    Args:
        mongo_uri: MongoDB connection URI.
        db_name: Database name.
        collection_name: Collection with SGB data.
        market_gold_price: Current 999 purity gold price (per gram).
        premium_threshold: Maximum acceptable premium (e.g., 0.03 for 3%).
    """
    ops = []

    cursor = sgb_collection.find({}, {"_id": 1, "LTP \n": 1})
    
    for doc in cursor:
        price = doc.get("LTP \n")
        if price is None or market_gold_price == 0:
            continue
        
        premium = (price - market_gold_price) / market_gold_price
        is_safe = premium <= premium_threshold
        
        ops.append(
            UpdateOne(
                {"_id": doc["_id"]},
                {"$set": {"safe_premium": is_safe, "premium_percent": round(premium * 100, 2)}}
            )
        )

    if ops:
        result = sgb_collection.bulk_write(ops)
        print(f"Updated {result.modified_count} SGB records with safe_premium field.")
    else:
        print("No valid SGB records to update.")

if __name__ == "__main__":
    premium_evaluator(market_gold_price=9853.0)
