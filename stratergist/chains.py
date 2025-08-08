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
from schemas import AnswerQuestion, ReviseAnswer

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
3. Recommend search queries to research information and improve your answer.""",
        ),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "Answer the user's question above using the required format."),
    ]
).partial(
    time=lambda: datetime.datetime.now().isoformat(),
)


first_responder_prompt_template = actor_prompt_template.partial(
    first_instruction="Provide a detailed breakdown of the stratergies providing reasons for each. No need to mention name of fund or bond, just the stratergies and how to divide the money between them."
)

first_responder = first_responder_prompt_template | llm.bind_tools(
    tools=[AnswerQuestion], tool_choice="AnswerQuestion"
)

revise_instructions = """Revise your previous answer using the new information:
    1. You MUST check if the amount of money you are allocating to each instrument is a feasable amount or not.
      - What I mean to say is if user has just 500 to invest monthly, then you cannot allocate 50 on bonds.
      Beacsue bonds don't trade at such low prices. Bonds are ateast 100+. Search and verify what the prices of instruments can be in the market.
      - Verify if the amount you are allocating is actually feasible to be invested in that instrument or not.
      - If you need search using the tools provided to you, but DONT give vauge answers.
      - Allcoate 0 if the instrument is not feasible to invest in.
    2. You MUST clearly mention the amount allocated to each instrument.
    3. Make sure to maintain the output format.
    4. Hedge the risks by diversifying the portfolio. Search for the best practices to do so. Specially for conservative stratergies, focus on fixed income.
    5. G-secs bonds are available at very low rates at 100+ rates so consider it while allocating.
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
