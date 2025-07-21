from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db import bonds_collection


# --- YTM Calculation Function ---
def calculate_ytm(face_value, price, coupon_rate, years_to_maturity):
    try:
        coupon = face_value * (coupon_rate / 100)
        ytm_guess = (coupon + ((face_value - price) / years_to_maturity)) / ((face_value + price) / 2)
        return round(ytm_guess * 100, 2)  # Return as percentage
    except:
        return None

# --- Main Process ---
def process_bonds():
    bonds = bonds_collection.find({"FACE_VALUE": {"$exists": True}, "LTP": {"$exists": True}, "COUPON_RATE": {"$exists": True}, "MATURITY_DATE": {"$exists": True}})
    updated = 0

    for bond in bonds:
        try:
            face_value = float(bond.get("FACE_VALUE", 1000))
            price = float(bond.get("LTP"))
            coupon_rate = float(bond.get("COUPON_RATE"))
            maturity_date = bond.get("MATURITY_DATE")
            today = datetime.today()

            if maturity_date <= today:
                continue

            years_to_maturity = (maturity_date - today).days / 365.0

            ytm = calculate_ytm(face_value, price, coupon_rate, years_to_maturity)

            if ytm is not None:
                bonds_collection.update_one(
                    {"_id": bond["_id"]},
                    {"$set": {"YTM": ytm}}
                )
                updated += 1
        except Exception as e:
            print(f"Error processing bond {bond["_id"]}: {e}")

    print(f"Updated {updated} bonds with YTM")

if __name__ == "__main__":
    process_bonds()
