from toolkit import fetch_risk_scores, fetch_return_scores
from langchain.agents import initialize_agent, Tool, AgentType
from dotenv import load_dotenv
import os
load_dotenv()
from langchain_community.chat_models import ChatOpenAI

tools = [
    Tool(
        name="fetch_risk_scores",
        func=fetch_risk_scores,
        description=(
            "Fetch the top N mutual funds sorted by ascending risk score (lowest risk first). "
            "Returns a JSON array of objects: [{'name':..., 'risk_score':...}, ...]. "
            "You can specify the number of funds to return using the 'top_n'"
            " parameter, which defaults to 5."
        ),
    ),
    Tool(
        name="fetch_return_scores",
        func=fetch_return_scores,
        description=(
            "Fetch the top N mutual funds sorted by descending return score (highest returns first). "
            "Returns a JSON array of objects: [{'name':..., 'return_score':...}, ...]. "
            "You can specify the number of funds to return using the 'top_n'"
            " parameter, which defaults to 5."
        ),
    ),
]

# SYSTEM  = """
# You are a Mutual‐Funds assistant.  
# Always respond with _only_ valid JSON.  
# Do not wrap your answer in markdown or prose.  
# If I ask for risk scores, return something like:  
#   [ { "name": "...", "risk_score": 2 }, … ]  
# If I ask for return scores, return:  
#   [ { "name": "...", "return_score": 85.3 }, … ]
# """

agent = initialize_agent(
    tools=tools,
    llm=ChatOpenAI(model="gpt-4o", temperature=0.2, openai_api_key=os.getenv("OPENAI_API_KEY")),
    agent=AgentType.OPENAI_FUNCTIONS,
    handle_parsing_errors=True,
    verbose=True
)