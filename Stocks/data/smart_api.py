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

    # Historical candle params
    params = {
        "exchange": "NSE",
        "symboltoken": "3045",  
        "interval": "ONE_DAY",
        "fromdate": "2025-07-16 13:00", 
        "todate": "2025-07-21 13:30"
    }

    result = obj.getCandleData(params)
    print("Historical Data:", result)

else:
    print("Login failed:", session_data)