# risk_model.py

def get_risk_thresholds(risk: str):
    """Returns return% target and volatility filter for a given risk profile."""
    risk = risk.lower()
    if risk == "low":
        return {"min_return": 8, "max_volatility": 0.8}
    elif risk == "moderate":
        return {"min_return": 12, "max_volatility": 1.1}
    elif risk == "high":
        return {"min_return": 18, "max_volatility": None}
    else:
        return {"min_return": 10, "max_volatility": 1.0}
