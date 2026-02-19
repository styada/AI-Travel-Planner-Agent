from langchain_community.tools import DuckDuckGoSearchRun

_search = DuckDuckGoSearchRun()

def web_search_tool(query: str) -> str:
    """Perform a web search using DuckDuckGo and return the results."""
    try:
        results = _search.run(query)
    except Exception as e:
        results = f"An error occurred while performing the web search: {e}"
    return results
