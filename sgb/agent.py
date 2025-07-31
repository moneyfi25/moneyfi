from .toolkit import fetch_top_sgbs
from langchain.agents import initialize_agent, Tool, AgentType
from dotenv import load_dotenv
import os
from langchain_community.chat_models import ChatOpenAI

load_dotenv()

# Define tools
tools = [
    Tool(
        name="fetch_top_sgbs",
        func=fetch_top_sgbs,
        description=(
            "Fetch the top N Sovereign Gold Bonds sorted by descending return score. "
            "Returns a list of dicts, each containing: "
            "{'symbol': ..., 'return_score': ..., 'last_traded_price': ..., 'premium_percent': ...}. "
            "You can specify the number of SGBs to return using the 'num' parameter, which defaults to 5."
        ),
    ),
]

# Lazy initialization of the agent
def get_sgb_agent():
    print("🔧 Initializing SGB Agent...")
    return initialize_agent(
        tools=tools,
        llm=ChatOpenAI(model="gpt-4o-mini", temperature=0.2, openai_api_key=os.getenv("OPENAI_API_KEY")),
        agent=AgentType.OPENAI_FUNCTIONS,
        handle_parsing_errors=True,
        verbose=True
    )