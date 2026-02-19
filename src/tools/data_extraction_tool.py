import os

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel
from src.tools.web_search_tool import web_search_tool
from typing import Optional, Any

class AgentResult(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    agent_name: str


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
    agent_name: str,
) -> AgentResult:
    structured_llm = _llm.with_structured_output(output_schema)
    current_query = query
    last_result = None

    for attempt in range(MAX_RETRIES):
        try:
            raw_results = search_web(current_query)
            result = structured_llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Extract from these search results:\n\n{raw_results}")
            ])

            if is_good_result(result):
                return AgentResult(success=True, data=result, agent_name=agent_name)

            last_result = result
            if attempt < MAX_RETRIES - 1:
                current_query = _generate_better_query(_llm, current_query, raw_results)
                print(f"{agent_name} attempt {attempt + 1} weak, new query: {current_query}")

        except Exception as e:
            print(f"{agent_name} attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                current_query = _generate_better_query(_llm, current_query, raw_results)

    # Exhausted retries
    if last_result:
        return AgentResult(success=False, data=last_result, error="Max retries exhausted, returning best available", agent_name=agent_name)
    
    return AgentResult(success=False, data=None, error="All attempts failed completely", agent_name=agent_name)