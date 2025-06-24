from langchain.agents import AgentExecutor, Tool
from langchain.chains.llm import LLMChain
from .prompt import REACT_PROMPT
from .tools import return_tools
from langchain.tools.render import render_text_description
from langchain_core.prompts import PromptTemplate
from langchain.agents.output_parsers import (
    ReActSingleInputOutputParser,
    ReActJsonSingleInputOutputParser,
)
from langchain.agents.format_scratchpad import format_log_to_str


def build_agent(chat):
    react_template = PromptTemplate.from_template(template=REACT_PROMPT)
    tools = return_tools()
    prompt = react_template.partial(
        tools=render_text_description(tools),
        tool_names=", ".join([t.name for t in tools]),
    )

    chat_model_with_stop = chat.bind(stop=["\nObservation"])
    agent = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_log_to_str(x["intermediate_steps"]),
        }
        | prompt
        | chat_model_with_stop
        | ReActJsonSingleInputOutputParser()
    )
    return AgentExecutor(
        tools=tools,
        agent=agent,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=50,
    )
