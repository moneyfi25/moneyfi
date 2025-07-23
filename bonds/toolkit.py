from langchain.tools import tool
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db import bonds_collection

# Assume your score_bond(bond: dict) -> dict with "bond_score" already exists

@tool
def compare_bonds_tool(top_n: int = 5) -> str:
    """
    Compares government and corporate bonds from the database, scores them,
    and returns the top N from each type with reasons based on scoring criteria.
    """

    bonds = list(bonds_collection.find())
    bonds = sorted(bonds, key=lambda x: x.get("score", 0), reverse=True)
    # Format output
    def format_top(bond_list):
        lines = [f"\n🔷 Top {int(top_n)} Bonds:"]
        for b in bond_list[:int(top_n)]:
            lines.append(
                f"- {b.get('SYMBOL', 'N/A')} | Score: {b['score']} | YTM: {b.get('YTM')}% | "
                f"Coupon: {b.get('COUPON_RATE')}% | Price: ₹{b.get('LTP')} | Rating: {b.get('CREDIT_RATING')} | "
                f"Type: {b.get('SERIES')} "
            )
        return "\n".join(lines)

    response = format_top(bonds)
    return response
