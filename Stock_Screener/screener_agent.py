from dotenv import load_dotenv
load_dotenv()

from .screener_tools import shortlist_stocks_by_risk
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", temperature=0.5)

tools = [shortlist_stocks_by_risk]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)
