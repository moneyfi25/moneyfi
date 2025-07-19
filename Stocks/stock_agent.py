from dotenv import load_dotenv
import os
from dotenv import load_dotenv
load_dotenv()
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from .stock_tools import get_stock_fundamentals, compare_stocks
from .advanced_stock_tools import (
    get_eps_growth,
    get_52w_momentum,
    get_volatility_label,
    get_dividend_consistency,
    get_insider_summary,
    compare_to_sector_pe,
    get_analyst_sentiment,
)

load_dotenv()

tools = [
    get_stock_fundamentals,
    get_eps_growth,
    get_52w_momentum,
    get_volatility_label,
    get_dividend_consistency,
    get_insider_summary,
    compare_to_sector_pe,
    get_analyst_sentiment,
    compare_stocks,
]

llm = ChatOpenAI(
    model="gpt-4o", 
    temperature=0.7
)

agent = initialize_agent(
    tools=tools,
    llm=ChatOpenAI(model="gpt-4o", temperature=0.2, openai_api_key=os.getenv("OPENAI_API_KEY")),
    agent=AgentType.OPENAI_FUNCTIONS,
    handle_parsing_errors=True,
    verbose=True
)

