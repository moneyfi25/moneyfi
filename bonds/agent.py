from toolkit import fetch_ytm, fetch_coupon, fetch_diff_ltp_face, fetch_maturity
from langchain.agents import initialize_agent, Tool, AgentType
from dotenv import load_dotenv
import os
load_dotenv()
from langchain_community.chat_models import ChatOpenAI

tools = [
    Tool(
        name="fetch_ytm",
        func=fetch_ytm,
        description="""
        Fetch all bonds and their YTM values.
        Returns a JSON array of objects:
        [{
        "SYMBOL": ..., 
        "YTM": ...},
         ...
        ].
        """
    ),
    Tool(
        name="fetch_coupon",
        func=fetch_coupon,
        description="""
        Fetch all bonds and their coupon rates.
        Returns a JSON array of objects:
        [{
        "SYMBOL": ..., 
        "COUPON_RATE": ...},
         ...
        ].
        """
    ),
    Tool(
        name="fetch_diff_ltp_face",
        func=fetch_diff_ltp_face,
        description="""
        Fetch all bonds and their difference between last traded price and face value.
        Returns a JSON array of objects:
        [{
        "SYMBOL": ..., 
        "diff_ltp_face": ...},
         ...
        ].
        """    ),
    Tool(
        name="fetch_maturity",
        func=fetch_maturity,
        description="""
        Fetch all bonds and their maturity dates.
        Returns a JSON array of objects:
        [{
        "SYMBOL": ..., 
        "MATURITY_DATE": ...},  
         ...
        ].
        """ 
    )
]

agent = initialize_agent(
    tools=tools,
    llm=ChatOpenAI(model="gpt-4o", temperature=0.2, openai_api_key=os.getenv("OPENAI_API_KEY")),
    agent=AgentType.OPENAI_FUNCTIONS,
    handle_parsing_errors=True,
    verbose=True
)