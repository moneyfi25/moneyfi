from SmartApi import SmartConnect
import pyotp
from datetime import datetime

# Required details
api_key = "DAeAdmOR"
client_code = "codeiwthjeery@gmail.com"
password = "cydgUs-wehhet-pymzo4"
totp_key = "9ea1833c-6a3f-4acb-9a9d-e4458e433396"  # TOTP secret from Angel One dashboard

# Initialize API
obj = SmartConnect(api_key=api_key)

# Generate TOTP
try:
    totp = pyotp.TOTP(totp_key).now()
except Exception as e:
    print("Invalid Token: The provided token is not valid.")
    raise e

# Login
data = obj.generateSession(client_code, password, totp)
auth_token = data['data']['jwtToken']
refresh_token = data['data']['refreshToken']

# Save access token for further use
obj.setAccessToken(auth_token)


# Historical data parameters
params = {
    "exchange": "NSE",              # or BSE
    "symboltoken": "3045",          # Get token for the symbol (e.g., RELIANCE)
    "interval": "FIVE_MINUTE",      # e.g. ONE_MINUTE, ONE_DAY, ONE_HOUR, etc.
    "fromdate": "2024-07-01 09:15", # format: yyyy-mm-dd HH:MM
    "todate": "2024-07-01 15:30"
}

# Convert to datetime
params["fromdate"] = datetime.strptime(params["fromdate"], "%Y-%m-%d %H:%M").isoformat()
params["todate"] = datetime.strptime(params["todate"], "%Y-%m-%d %H:%M").isoformat()

# Get data
historical_data = obj.getCandleData(params)
print(historical_data)
