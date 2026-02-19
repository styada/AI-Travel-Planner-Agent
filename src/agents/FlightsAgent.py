import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field
from models.ResearchResults import FlightOption
from models.TripState import TripState
from tools.web_search_tool import web_search_tool


class FlightResults(BaseModel):
    flights: list[FlightOption] = Field(
        description="List of flight options that match the trip request criteria. Each option includes details such as airline, departure and arrival times, price, origin, destination, duration, booking URL, and class type."
    )
    

_llm = ChatOllama(model=os.getenv("OLLAMA_TEXT_MODEL"), temperature=0)

_structured_llm = _llm.with_structured_output(FlightResults) # Super fucking cool btw

SYSTEM_PROMPT = """
    You will be given raw web search results about flights.
    Extract concrete flight options from the results and return them.

    Rules:
    - Only include flights with a real airline name
    - Price must be a number in USD
    - If booking URL is not found, leave it null
    - Return at most 5 options
    - Do not invent flights that are not in the search results
"""

def flights_agent(state: TripState) -> dict:
    req = state.trip_request
    
    query = {
        f"""
        Find flights from {req.origin} to {req.destination}
        departing around {req.start_date} and returning around {req.end_date}
        show a range of prices and airlines, and include booking URLs if available.
        """
    }
    
    raw_response = web_search_tool(query)
    
    structured_response: FlightResults = _structured_llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Extract flight options from these search results:\n\n{raw_response}")
    ])
    
    return{
        "research": {
            "flights": [f.model_dump() for f in structured_response.flights]
        }
    }