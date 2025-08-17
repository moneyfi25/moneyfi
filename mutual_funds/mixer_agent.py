from dotenv import load_dotenv
import os
from langchain_community.chat_models import ChatOpenAI

load_dotenv()

def initialize_mixer_agent():
    return ChatOpenAI(
        model="gpt-4o",
        temperature=0.2,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

def invoke_mixer_agent(input_query):
    mixer_agent = initialize_mixer_agent()
    response = mixer_agent.predict(input_query)
    return response