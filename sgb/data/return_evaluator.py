from pymongo import MongoClient, UpdateOne
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db import sgb_collection

def calculate_and_store_scores(
    weight_annual: float = 70.0,
    weight_monthly: float = 30.0,
    score_field: str = "score"
):
    """
    Computes a weighted return score for every document and writes it back to MongoDB.
    
    Args:
        mongo_uri:     MongoDB connection URI.
        db_name:       Database name.
        collection_name: Collection holding SGB return docs.
        weight_annual: Weight for the 365-day return.
        weight_monthly: Weight for the 30-day return.
        score_field:   Field name under which to store the computed score.
    """
    ops = []
    # Only pull minimal fields for speed
    cursor = sgb_collection.find({}, {"365 D % CHNG \n": 1, "30D   %CHNG \n": 1})
    
    for doc in cursor:
        r365 = doc.get("365 D % CHNG \n")
        r30  = doc.get("30D   %CHNG \n")
        
        if r365 is None or r30 is None:
            continue
        
        score = weight_annual * r365 + weight_monthly * r30
        
        ops.append(
            UpdateOne(
                {"_id": doc["_id"]},
                {"$set": {score_field: score}}
            )
        )
    
    if not ops:
        print("No documents to update.")
        return
    
    result = sgb_collection.bulk_write(ops)
    print(f"Matched:  {result.matched_count}")
    print(f"Modified: {result.modified_count}")

if __name__ == "__main__":
    calculate_and_store_scores(
        weight_annual=70.0,
        weight_monthly=30.0,
        score_field="return_score"
    )


