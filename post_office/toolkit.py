from typing import Union
import json, ast
from langchain_core.tools import tool
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from data.vector_db import load_post_office_vectorstore

# reload your vector store & build the QA chain once
vectordb = load_post_office_vectorstore("post_office_schemes_db")
retriever = vectordb.as_retriever(search_type="similarity", search_kwargs={"k": 3})
qa_chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(model="gpt-4o", temperature=0),
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=False
)

@tool
def find_post_office_schemes(raw_input: str) -> str:
    """ Find Post Office schemes based on user input.
    Accepts:
      - a JSON string (double quotes)
      - a Python literal string (single or double quotes)
      - a simple key:value string (e.g. "time_horizon_years:
      5, user_age: 30, beneficiary: 'general'") 
     Returns a list of dicts:
      - scheme: str
      - expected_interest: float
      - suitability: str
    """
    # 1) Try strict JSON
    try:
        params = json.loads(raw_input)
    except json.JSONDecodeError:
        # 2) Fallback to Python literal
        try:
            params = ast.literal_eval(raw_input)
        except Exception:
            # 3) Fallback to manual key:value parsing
            params = {}
            for piece in raw_input.split(","):
                if ":" in piece:
                    k, v = piece.split(":", 1)
                    params[k.strip()] = v.strip().strip("'\"")

    # 4) Extract with defaults
    horizon     = int(params.get("time_horizon_years", 0))
    user_age    = int(params.get("user_age", 0))
    beneficiary = params.get("beneficiary", "general")

    # 5) Build a natural-language query
    query = (
        """Recommend Post Office schemes for a {horizon}-year horizon, 
        for a {beneficiary} investor
         Return a list of dicts:
      - scheme: str
      - expected_interest: float
      - suitability: str """
    )

    # 6) Run your RetrievalQA chain
    response = qa_chain.invoke(query)
    print('\n')
    print(response)
    print('\n')
    return response

