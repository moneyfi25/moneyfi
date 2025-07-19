from langchain.agents import initialize_agent, Tool, AgentType
from langchain.chat_models import ChatOpenAI
from .toolkit import find_post_office_schemes
from dotenv import load_dotenv
load_dotenv()


tools = [
    Tool(
        name="post_office_scheme_finder",
        func=find_post_office_schemes,
        description=(
            "Use this to answer questions about Post Office schemes. "
            "Returns the best matches."
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
