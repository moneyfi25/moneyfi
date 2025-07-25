# from langchain.document_loaders import PyPDFLoader

# loader = PyPDFLoader("KIM and Application Form - Axis Multicap Fund.pdf")
# pages = loader.load()  # list of Document objects, with .page_content

import pdfplumber
import pandas as pd

tables = []
with pdfplumber.open("KIM and Application Form - Axis Multicap Fund.pdf") as pdf:
    for page in pdf.pages:
        for table in page.extract_tables():
            # first row is header
            df = pd.DataFrame(table[1:], columns=table[0])
            tables.append(df)

for i, df in enumerate(tables):
    print(f"\n--- Table {i} ---")
    print(df.head())
