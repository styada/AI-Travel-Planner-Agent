import logging
from pydantic import BaseModel, Field
from src.models.ResearchResults import FlightOption
from src.models.TripState import TripState
from src.tools.data_extraction_tool import extract_with_retry

logger = logging.getLogger(__name__)


class FlightResults(BaseModel):
    flights: list[FlightOption] = Field(
        description="List of flight options that match the trip request criteria. Each option includes details such as airline, departure and arrival times, price, origin, destination, duration, booking URL, and class type."
    )
    

SYSTEM_PROMPT = """
    You are a flight research specialist.
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
    logger.info("FlightsAgent: Starting flight research")
    req = state.trip_request
    query = f"""
        Find flights from {req.origin} to {req.destination}
        departing around {req.start_date} and returning around {req.end_date}
        show a range of prices and airlines, and include booking URLs if available.
        """
    logger.debug(f"FlightsAgent: Search query - {query.strip()}")
    
    result = extract_with_retry(
        query=query,
        system_prompt=SYSTEM_PROMPT,
        output_schema=FlightResults,
        is_good_result=lambda r: bool(r.flights) and any(f.price > 0 for f in r.flights),
        agent_name="FlightsAgent"
    )

    flights = [f.model_dump() for f in result.data.flights] if result.success and result.data else []
    logger.info(f"FlightsAgent: Found {len(flights)} flight options")
    return {"research": {
        "flights": flights},
        "failed_agents": state.failed_agents + ([result.agent_name] if not result.success else [])
    }