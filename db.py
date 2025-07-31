from pymongo import MongoClient
from dotenv import load_dotenv
import os
load_dotenv()

uri = os.getenv("MONGO_URI")
client = MongoClient(uri)
db = client["MoneyFi"]
mutual_funds_collection = db["mutual_funds"]
sgb_collection = db["gold_bonds"]
bonds_collection = db["bonds"]
index_collection = db["index_data"]
etf_collection = db["etf_data"]
insurance_collection = db["insurance_data"]