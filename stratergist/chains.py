import datetime
from dotenv import load_dotenv
load_dotenv()
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers.openai_tools import (
    JsonOutputToolsParser,
    PydanticToolsParser,
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from .schemas import AnswerQuestion, ReviseAnswer

llm = ChatOpenAI(model="o4-mini")
parser = JsonOutputToolsParser(return_id=True)
parser_pydantic = PydanticToolsParser(tools=[AnswerQuestion])

actor_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an expert financial strategist.
Current time: {time}

Instructions:
1. {first_instruction}
2. After answering, reflect and critique your response. Be rigorous and suggest concrete improvements.
3. Recommend specific search queries to research current market strategies and further improve your answer.
4. Suggest the best possible allocation options for both lumpsum and monthly investment amounts, ensuring all recommendations are actionable and practical.
5. Follow all minimum investment rules and output schema strictly.
""",
        ),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "Answer the user's question above using the required format."),
    ]
).partial(
    time=lambda: datetime.datetime.now().isoformat(),
)

first_responder_prompt_template = actor_prompt_template.partial(
    first_instruction=(
        "Provide a detailed investment strategy based on the user's lumpsum and monthly investment amounts. "
        "If the lumpsum is 0, only consider monthly investment. "
        "Ensure allocations are realistic, actionable, and comply with all minimum investment requirements."
    ),
)

first_responder = first_responder_prompt_template | llm.bind_tools(
    tools=[AnswerQuestion], tool_choice="AnswerQuestion"
)

revise_instructions = """Revise your previous answer using the new information:
1. These are the minimum investment amounts for each instrument. Your recommendations for each instrument must be at least the minimum and not exceed the available monthly_investment or lumpsum_investment:
    - Mutual Funds: minimum Rs. 100
    - ETFs: minimum Rs. 100
    - Bonds: minimum Rs. 100
    - Sovereign Gold Bonds: minimum Rs. 10,500 (current 999 gold price)
2. Clearly specify the percentage allocation for each instrument in both lumpsum and monthly investments. All percentages must be integers and each allocation must sum to 100%.
3. Strictly follow the output format as specified in the schema.
4. Diversify the portfolio to hedge risks. For conservative strategies, prioritize fixed income instruments (Bonds, SGBs) over growth instruments.
5. Use realistic, actionable allocations and ensure all recommendations are practical for the user's investment amounts.
"""

revisor = actor_prompt_template.partial(
    first_instruction=revise_instructions
) | llm.bind_tools(tools=[ReviseAnswer], tool_choice="ReviseAnswer")


# if __name__ == "__main__":
#     human_message = HumanMessage(
#         content="Coin out 3 stratergies to imporve investment of customer by balancing risk and returns."
#          "Available instruemnts are mutual funds, bonds and ETFs. If there a fixed amount to invest monthly say 10,000,"
#           "What should be the stratergy to divide the money between these instruments?"
#     )
#     chain = (
#         first_responder_prompt_template
#         | llm.bind_tools(tools=[AnswerQuestion], tool_choice="AnswerQuestion")
#         | parser_pydantic
#     )

#     res = chain.invoke(input={"messages": [human_message]})
#     print(res)
