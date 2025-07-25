from toolkit import fetch_returns
from langchain.agents import initialize_agent, Tool, AgentType
from dotenv import load_dotenv
import os
load_dotenv()
from langchain_community.chat_models import ChatOpenAI

tools = [
    Tool(
        name="fetch_returns_tool",
        func=fetch_returns,
        description=(
            "Fetch all the mutual funds returns. "
            "Returns a JSON array of objects: [{'fund_name':..., '1_week_return':..., '1_month_return':..., "
            "'3_month_return':..., '6_month_return':..., '1_year_return':...}, ...]. "
            "This tool provides a comprehensive overview of mutual fund performance over various time periods."
        ),
    )
]

agent = initialize_agent(
    tools=tools,
    llm=ChatOpenAI(model="gpt-4o", temperature=0.2, openai_api_key=os.getenv("OPENAI_API_KEY")),
    agent=AgentType.OPENAI_FUNCTIONS,
    handle_parsing_errors=True,
    verbose=True
)