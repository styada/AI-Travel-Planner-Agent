import os

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel
from src.tools.web_search_tool import web_search_tool


_llm = ChatOllama(model=os.getenv("OLLAMA_TEXT_MODEL"), temperature=0)

MAX_RETRIES = 3


def _generate_better_query(llm, previous_query: str, previous_results: str) -> str:
    response = llm.invoke([
        SystemMessage(content="""You are a search query optimizer.
        Given a query that returned poor results, generate a better one.
        Return ONLY the search query string, nothing else."""),
        HumanMessage(content=f"""
            Previous query: {previous_query}
            Previous results: {previous_results[:500]}
            Generate a better search query.""")
    ])
    return response.content.strip()


def extract_with_retry(
    query: str,
    system_prompt: str,
    output_schema: type[BaseModel],
    is_good_result: callable,
) -> BaseModel:
    """
    Shared retry loop for all specialist agents.
    - Searches the web
    - Asks LLM to extract structured data
    - Retries with LLM-generated query if results are poor
    """
    structured_llm = _llm.with_structured_output(output_schema)
    current_query = query
    last_result = None

    for attempt in range(MAX_RETRIES):
        raw_results = web_search_tool(current_query)

        try:
            result = structured_llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Extract from these search results:\n\n{raw_results}")
            ])

            if is_good_result(result):
                return result

            last_result = result
            if attempt < MAX_RETRIES - 1:
                current_query = _generate_better_query(_llm, current_query, raw_results)
                print(f"Attempt {attempt + 1} weak, new query: {current_query}")

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                current_query = _generate_better_query(_llm, current_query, raw_results)

    return last_result