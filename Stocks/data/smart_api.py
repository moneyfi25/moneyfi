from SmartApi import SmartConnect
import pyotp
from datetime import datetime

# Required details
api_key = "xHU58PcC"
client_code = "AAAQ444832"
password = "2710"
totp_key = "NIIRE3UIHLHHLXJSUWNQEJ7XEM"  # TOTP secret from Angel One dashboard

# Login
obj = SmartConnect(api_key=api_key)
totp = pyotp.TOTP(totp_key).now()
session_data = obj.generateSession(client_code, password, totp)

if session_data and "data" in session_data:
    jwt_token = session_data["data"]["jwtToken"]
    refresh_token = session_data["data"]["refreshToken"]

    # No need to access .session.headers manually!
    print("Login successful")

    historical_data = obj.getCandleData({
        "exchange": "NSE",
        "symboltoken": "2885",  # ✅ not `token` – must be `symboltoken`
        "interval": "ONE_DAY",
        "fromdate": "2025-07-15 09:15",
        "todate": "2025-07-21 15:30"
    })

    print("Historical Data:", historical_data)

else:
    print("Login failed:", session_data)