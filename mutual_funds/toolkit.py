from typing import Union
import json, ast
from langchain_core.tools import tool
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from data.vector_db import load_mutual_funds_vectorstore

vectordb = load_mutual_funds_vectorstore("mutual_funds_db")
retriever = vectordb.as_retriever(search_type="similarity", search_kwargs={"k": 10})
qa_chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(model="gpt-4o", temperature=0),
    chain_type="map_reduce",
    retriever=retriever,
    return_source_documents=False
)

@tool
def screen_mutual_funds() -> str:
    """ Filter Mutual Funds based on 1y return.
     Returns a list of dicts:
      - scheme_name: str
      - return_1y_regular: float
      - return_3y_regular: float
      - return_5y_regular: float
    """

    # 5) Build a natural-language query
    query = (
        f"""Filter Mutual Funds with a 1-year return greater than 3%.
      - scheme_name: str
      - return_1y_regular: float
      - return_3y_regular: float
      - return_5y_regular: float"""
    )

    # 6) Run the QA chain and return results
    response = qa_chain.invoke({"query": query})
    return response['result'] if isinstance(response, dict) else str(response)