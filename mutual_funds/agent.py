from toolkit import screen_mutual_funds
from langchain.agents import initialize_agent, Tool, AgentType
from dotenv import load_dotenv
load_dotenv()
from langchain.chat_models import ChatOpenAI

tools = [
    Tool(
        name="screen_mutual_funds",
        func=screen_mutual_funds,
        description=(
            "Use this to filter Mutual Funds based on 1-year return. "
            "Returns a list of dicts with scheme details."
        ),
    )
]

agent = initialize_agent(
    tools=tools,
    llm=ChatOpenAI(model="gpt-4o", temperature=0.2),
    agent=AgentType.OPENAI_FUNCTIONS,
    handle_parsing_errors=True,
    verbose=True,
)