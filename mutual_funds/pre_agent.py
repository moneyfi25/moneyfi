from dotenv import load_dotenv
import os
from langchain_community.chat_models import ChatOpenAI

load_dotenv()

# Initialize the ChatOpenAI model directly
def initialize_pre_agent():
    return ChatOpenAI(
        model="gpt-4o",
        temperature=0.2,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

def invoke_pre_agent(input_query):
    pre_agent = initialize_pre_agent()
    response = pre_agent.predict(input_query)
    return response