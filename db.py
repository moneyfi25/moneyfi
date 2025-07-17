from pymongo import MongoClient
from dotenv import load_dotenv
import os
load_dotenv()

uri = os.getenv("MONGO_URI")
client = MongoClient(uri)
db = client["MoneyFi"]
mutual_funds_collection = db["mutual_funds"]