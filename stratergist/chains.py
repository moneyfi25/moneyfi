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
            """You are expert financial stratergist.
Current time: {time}

1. {first_instruction}
2. Reflect and critique your answer. Be severe to maximize improvement.
3. Recommend search queries to research information regarding stratergies used in market and improve your answer.
4. Give the best possible options for the lumpsum and monthly investment amounts.""",
        ),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "Answer the user's question above using the required format."),
    ]
).partial(
    time=lambda: datetime.datetime.now().isoformat(),
)


first_responder_prompt_template = actor_prompt_template.partial(
    first_instruction="Provide a detiled stratergy based on lumpsum and monthly investment amounts. If the lumpsum is 0, then only consider monthly investment.",
)

first_responder = first_responder_prompt_template | llm.bind_tools(
    tools=[AnswerQuestion], tool_choice="AnswerQuestion"
)

revise_instructions = """Revise your previous answer using the new information:
    1. These are the minimum investment amounts for each instrument. Use this information to make sure your recommendations are
    priced less than monthly_investment or lumpsum_investment:
        - Mutual Funds: starts from Rs. 100
        - ETFs: starts from Rs. 100
        - Bonds: starts from Rs. 100+
        - Sovereign Gold Bonds: starts from Rs. 10,500+ (Current 999 gold price)
    2. You MUST clearly mention the percentage of money allocated to each instrument in lumpsum and monthly investment.
    3. You MUST maintain the output format as specified in the schema.
    4. Hedge the risks by diversifying the portfolio. Search for the best practices to do so. Specially for conservative stratergies, focus on fixed income.
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
