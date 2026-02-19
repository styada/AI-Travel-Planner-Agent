import logging
from langchain_community.tools import DuckDuckGoSearchRun

logger = logging.getLogger(__name__)

def _get_search():
    return DuckDuckGoSearchRun()

def web_search_tool(query: str) -> str:
    """Perform a web search using DuckDuckGo and return the results."""
    logger.info(f"Executing web search: {query[:100]}...")
    try:
        _search = _get_search()
        results = _search.run(query)
        logger.debug(f"Web search returned {len(results)} characters")
        return results
    except Exception as e:
        logger.error(f"Web search failed for query '{query[:80]}...': {str(e)}")
        results = f"An error occurred while performing the web search: {e}"
        return results
