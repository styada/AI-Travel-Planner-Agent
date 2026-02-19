import os
import logging
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel
from src.tools.web_search_tool import web_search_tool
from typing import Optional, Any

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AgentResult(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    agent_name: str


def get_llm():
    return ChatGoogleGenerativeAI(model=os.getenv("GOOGLE_GEMINI_MODEL"), temperature=0)

MAX_RETRIES = 3


def _generate_better_query(llm, previous_query: str, previous_results: str) -> str:
    logger.debug(f"Generating improved query for: {previous_query[:80]}...")
    response = llm.invoke([
        SystemMessage(content="""You are a search query optimizer.
        Given a query that returned poor results, generate a better one.
        Return ONLY the search query string, nothing else."""),
        HumanMessage(content=f"""
            Previous query: {previous_query}
            Previous results: {previous_results[:500]}
            Generate a better search query.""")
    ])
    improved_query = response.content.strip()
    logger.debug(f"Improved query: {improved_query}")
    return improved_query


def extract_with_retry(
    query: str,
    system_prompt: str,
    output_schema: type[BaseModel],
    is_good_result: callable,
    agent_name: str,
) -> AgentResult:
    logger.info(f"[{agent_name}] Starting extraction with query: {query[:100]}...")
    llm = get_llm()
    structured_llm = llm.with_structured_output(output_schema)
    current_query = query
    last_result = None

    for attempt in range(MAX_RETRIES):
        raw_results = None
        try:
            logger.debug(f"[{agent_name}] Attempt {attempt + 1}/{MAX_RETRIES} - Searching: {current_query[:80]}...")
            raw_results = web_search_tool(current_query)
            logger.debug(f"[{agent_name}] Search returned {len(raw_results)} characters")
            
            logger.debug(f"[{agent_name}] Invoking LLM for structured extraction")
            result = structured_llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Extract from these search results:\n\n{raw_results}")
            ])
            logger.debug(f"[{agent_name}] LLM extraction complete")

            if is_good_result(result):
                logger.info(f"[{agent_name}] Extraction successful on attempt {attempt + 1}")
                return AgentResult(success=True, data=result, agent_name=agent_name)

            last_result = result
            logger.warning(f"[{agent_name}] Attempt {attempt + 1} returned weak results, retrying...")
            if attempt < MAX_RETRIES - 1 and raw_results:
                current_query = _generate_better_query(llm, current_query, raw_results)

        except Exception as e:
            logger.error(f"[{agent_name}] Attempt {attempt + 1} failed: {str(e)}")
            if attempt < MAX_RETRIES - 1 and raw_results:
                logger.info(f"[{agent_name}] Attempting query refinement after error")
                current_query = _generate_better_query(llm, current_query, raw_results or "")

    # Exhausted retries
    logger.error(f"[{agent_name}] Exhausted all {MAX_RETRIES} retry attempts")
    if last_result:
        logger.warning(f"[{agent_name}] Returning best available result after retries exhausted")
        return AgentResult(success=False, data=last_result, error="Max retries exhausted, returning best available", agent_name=agent_name)
    
    logger.error(f"[{agent_name}] Complete failure - no results obtained")
    return AgentResult(success=False, data=None, error="All attempts failed completely", agent_name=agent_name)