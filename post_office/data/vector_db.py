from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.docstore.document import Document
from .schemes import schemes
import chromadb
from load_dotenv import load_dotenv 
load_dotenv()

docs = [
    Document(
        page_content=scheme["description"],
        metadata={
            "scheme": scheme["scheme"],
            "interest": scheme["interest"],
            "term_years": scheme["term_years"],
            "liquidity": scheme["liquidity"],
        }
    )
    for scheme in schemes
]
# 3) Embed + push into Chroma
embeddings = OpenAIEmbeddings()  
vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=embeddings,
    persist_directory="post_office_schemes_db"
)
# 4) Persist to disk
vectorstore.persist()
print("✔ Schemes indexed to vector store.")

def load_post_office_vectorstore(persist_dir: str) -> Chroma:
    """
    Reloads the Chroma vector store you previously persisted.
    Returns the Chroma instance, whose retriever you can plug into any chain.
    """
    embeddings = OpenAIEmbeddings()
    vectordb = Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings
    )
    return vectordb


