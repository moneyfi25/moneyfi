from sgb.main import sgb_tool
from mutual_funds.main import mutual_funds_tool
from bonds.main import bonds_tool
from langchain.agents import initialize_agent, Tool, AgentType
from dotenv import load_dotenv
import os
from langchain_community.chat_models import ChatOpenAI

load_dotenv()

# Define tools
tools = [
    # Tool(
    #     name="sgb_tool",
    #     func=sgb_tool,
    #     description=(
    #         "Use this tool to find the best Sovereign Gold Bond (SGB) for hedging a growth portfolio, "
    #         "fighting inflation, and achieving good returns. "
    #         "It will return the top SGB based on the provided criteria."
    #     ),
    # ),
    Tool(
        name="mutual_funds_tool",
        func=mutual_funds_tool,
        description=(
            "Use this tool to find the best mutual funds based on risk and return scores. "
            "It will return the top mutual funds according to the user's investment goals, "
            "Take user_inputs as an argument, which includes objective, horizon, age, monthly investment, risk, fund type, and special preferences."
        ),
    ),
    Tool(
        name="bonds_tool",
        func=bonds_tool,
        description=(
            "Use this tool to find the best bonds based on yield to maturity (YTM), "
            "coupon rates, and other bond metrics. "
            "take user_inputs as an argument, which includes horizon, monthly investment, risk and special preferences."
        ),
    )
]

# Lazy initialization of the agent
def get_agent():
    return initialize_agent(
        tools=tools,
        llm=ChatOpenAI(model="gpt-4o", temperature=0.2, openai_api_key=os.getenv("OPENAI_API_KEY")),
        agent=AgentType.OPENAI_FUNCTIONS,
        handle_parsing_errors=True,
        verbose=True
    )