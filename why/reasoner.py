from dotenv import load_dotenv
import os
from langchain_community.chat_models import ChatOpenAI

load_dotenv()

def initialize_reasoner_agent():
    return ChatOpenAI(
        model="gpt-5-mini",
        temperature=1.0,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

def invoke_reasoner_agent(input_query):
    reasoner_agent = initialize_reasoner_agent()
    response = reasoner_agent.predict(input_query)
    return response