from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o",  
    temperature=0.7
)

prompt = PromptTemplate(
    input_variables=["amount", "duration", "target", "risk"],
    template="""
You are a financial advisor. Based on the following information, provide a detailed and actionable investment strategy in structured JSON format:

- Monthly Investment Amount: ₹{amount}
- Investment Duration: {duration} years
- Target Amount: ₹{target}
- Risk Appetite: {risk}

Your response must be a valid JSON object with the following structure:

{{
  "strategy_summary": "A short overview of the strategy and rationale.",
  "expected_return": "Expected annual return (%)",
  "allocation": {{
    "Investment type 1 (ex - stocks)": [
      {{
        "name": "product Name (ex- ADANIENT)",
        "percentage": y,
        "reason": "Why this is selected"
      }}
    ],
    "Investment type 2": [
      {{
        "name": "product name",
        "percentage": x,
        "reason": "Why this is selected"
      }}
    ],
    ... (add more types as needed)
  }},
  "liquidity_notes": "Comment on liquidity and lock-in periods if any.",
  "rebalancing": "Recommended rebalancing frequency (e.g., yearly, quarterly).",
  "risk_profile_explanation": "Explain how the portfolio matches the user's risk appetite."
}}

Respond with only this JSON object — no extra text or markdown.
"""
)

# Create the LLM chain
chain = prompt | llm

# Sample input
input_data = {
    "amount": "5000",
    "duration": "5 years",
    "target": "1000000",
    "risk": "moderate"
}

# Run the agent
resonse = chain.invoke(input_data)

print("\n✅ GPT Agent Response:\n")
print(resonse.content)
