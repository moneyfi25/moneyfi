from sbg.main import sgb_tool
from mutual_funds.main import mutual_funds_tool
from stocks.main import stock_tool
from stock_scrneer.main import stock_screen_tool
from langchain.agents import initialize_agent, Tool, AgentType
from dotenv import load_dotenv
import os
load_dotenv()
from langchain_community.chat_models import ChatOpenAI

tools = [
    Tool(
        name="sgb_tool",
        func=sgb_tool,
        description=(
            "Use this tool to find the best Sovereign Gold Bond (SGB) for hedging a growth portfolio, "
            "fighting inflation, and achieving good returns. "
            "It will return the top SGB based on the provided criteria."
        ),
    ),
    Tool(
        name="mutual_funds_tool",
        func=mutual_funds_tool,
        description=(
            "Use this tool to find the best mutual funds based on risk and return scores. "
            "It will return the top mutual funds sorted by the specified criteria."
        ),
    ),
    # Tool(
    #     name="stock_tool",
    #     func=stock_tool,
    #     description=(
    #         "Use this tool to find the best stock among a set of scrneed stocks based on user criteria. "
    #         "It will return the top stock suggestion based on the provided query."
    #     ),
    # ),
    # Tool(
    #     name="stock_screen_tool",
    #     func=stock_screen_tool,
    #     description=(
    #         "Use this tool to screen stocks based on user-defined criteria like fundamentals, growth, etc. "
    #         "It will return the stocks that match the specified query."
    #     ),
    # ),
]

agent = initialize_agent(
    tools=tools,
    llm=ChatOpenAI(model="gpt-4o", temperature=0.2, openai_api_key=os.getenv("OPENAI_API_KEY")),
    agent=AgentType.OPENAI_FUNCTIONS,
    handle_parsing_errors=True,
    verbose=True
)