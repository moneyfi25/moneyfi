from .toolkit import fetch_short_term_returns, fetch_risk_and_volatility_parameters, fetch_long_term_returns, fetch_fees_and_details
from langchain.agents import initialize_agent, Tool, AgentType
from dotenv import load_dotenv
import os
load_dotenv()
from langchain_community.chat_models import ChatOpenAI

tools = [
    Tool(
        name="fetch_short_term_returns_tool",
        func=fetch_short_term_returns,
        description=(
            """Fetch all the etfs and their short term returns -
            which includes returns for 1 week, 1 month, 3 months, 6 months, and 1 year.
            Returns a JSON array of objects: 
            [{"fund_name":...,
              "1_week_return": ...,
              "1_month_return": ...,
              "3_month_return": ...,
              "6_month_return": ...,
              "1_year_return": ...},
              ...
            ]."""
        ),
    ),
    Tool(
        name="fetch_long_term_returns_tool",
        func=fetch_long_term_returns,
        description=(
            """Fetch all the etfs and their long term returns -
            which includes returns for 3 years, 5 years, and 10 years.
            Returns a JSON array of objects: 
            [{"fund_name":...,
              "3_year_return": ...
              "5_year_return": ...,
              "10_year_return": ...]},
              ...
            ]."""
        )
    ),
    Tool(
        name="fetch_risk_and_volatility_parameters_tool",
        func=fetch_risk_and_volatility_parameters,
        description=(
            """Fetch all the etfs and their risk parameters -
            which includes Sharpe ratio, Sortino ratio, Beta, Alpha, Standard Deviation, Information ratio and r-squared.
            Returns a JSON array of objects: 
            [{"fund_name":...,
              "sharpe_ratio": ...,
              "sortino_ratio": ...,
              "beta": ...,
              "alpha": ...,
              "standard_deviation": ...,
              "information_ratio": ...,
              "r_squared": ...},
              ...
            ]."""
        ),
    ),
    Tool(
        name="fetch_fees_and_details_tool",
        func=fetch_fees_and_details,
        description=(
            """Fetch all the etfs and their fees and details -
            which includes expense ratio, category, minimum investment, fund manager and exit load.
            Returns a JSON array of objects: 
            [{"fund_name":...,
              "category": ...,
              "expense_ratio": ...,
              "minimum_investment": ...,
              "exit_load": ...,
              "fund_manager": ...},
              ...
            ]."""
        ),
    ),
]

def get_etfs_agent():
    """Lazy initialization of the etfs agent."""
    print("🔧 Initializing etfs Agent...")
    return initialize_agent(
        tools=tools,
        llm=ChatOpenAI(model="gpt-4o-mini", temperature=0.2, openai_api_key=os.getenv("OPENAI_API_KEY")),
        agent=AgentType.OPENAI_FUNCTIONS,
        handle_parsing_errors=True,
        verbose=True
    )