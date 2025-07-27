import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db import bonds_collection


def score_bond(bond):
    score = 0

    # --- YTM Scoring ---
    ytm = bond.get("YTM", 0)
    if ytm > 12:
        ytm_score = 0
    elif ytm > 9:
        ytm_score = 20
    elif ytm > 7.5:
        ytm_score = 15
    elif ytm > 6:
        ytm_score = 10
    else:
        ytm_score = 5
    score += ytm_score

    # --- Coupon Rate Scoring ---
    coupon = bond.get("COUPON_RATE", 0)
    if coupon > 7:
        coupon_score = 15
    elif coupon >= 6:
        coupon_score = 10
    else:
        coupon_score = 5
    score += coupon_score

    # --- Price vs Face Value Scoring ---
    price = bond.get("LTP", 0)
    face = bond.get("FACE_VALUE", 1000)

    if face == 0:
        price_score = 0 
    else:
        price_diff_pct = ((price - face) / face) * 100

        if price_diff_pct <= -2:
            price_score = 15
        elif price_diff_pct <= 2:
            price_score = 13
        elif price_diff_pct <= 5:
            price_score = 10
        elif price_diff_pct <= 10:
            price_score = 5
        else:
            price_score = 0

    score += price_score


    # --- Maturity Scoring ---
    from datetime import datetime
    maturity_date = bond.get("MATURITY_DATE")
    if isinstance(maturity_date, str):
        maturity_date = datetime.strptime(maturity_date, "%d-%m-%Y")
    years_left = (maturity_date - datetime.today()).days / 365.25 if maturity_date else 0
    if 2 <= years_left <= 5:
        maturity_score = 15
    elif 5 < years_left <= 7:
        maturity_score = 10
    elif years_left < 2:
        maturity_score = 8
    else:
        maturity_score = 5
    score += maturity_score

    # Final score (out of 100)
    bond["bond_score"] = score
    return bond

if __name__ == "__main__":
    bonds = list(bonds_collection.find())
    # for bond in bonds:
    #     scored = score_bond(bond)
    #     bonds_collection.update_one({"_id": bond["_id"]}, {"$set": {"score": scored["bond_score"]}})