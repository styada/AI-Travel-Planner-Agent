from pydantic import BaseModel, Field
from models.ResearchResults import TransportationOption
from models.TripState import TripState
from tools.data_extraction_tool import extract_with_retry


class TransportationResults(BaseModel):
    transportation_options: list[TransportationOption] = Field(
        description="List of local transportation options in the destination. Each option includes details such as type, price, duration, departure and arrival times, origin, destination, booking URL, contact information, and class type."
    )


SYSTEM_PROMPT = """
    You are a local transportation research specialist.
    You will be given web search results about transportation options.
    Extract concrete transportation options from the results and return them.

    Rules:
    - Only include transportation services with a real name/type
    - Price must be a number in USD (if available, otherwise null)
    - If booking URL is not found, leave it null
    - Return at most 5 options
    - Duration should be in a readable format (e.g., "30 minutes", "2 hours")
    - Include a variety of transportation types (metro, bus, train, taxi, rideshare, etc.)
    - Include departure/arrival times and class type if available
    - Do not invent transportation services that are not in the search results
"""

def transportation_agent(state: TripState) -> dict:
    req = state.trip_request
    query = f"""
        Find local transportation options in {req.destination}.
        Look for public transportation (metro, buses, trains), taxis, rideshare services, and other transit options.
        Include pricing, routes, schedules, and booking URLs if available.
        Focus on transportation within the city and options for getting around during the trip.
        Look for options that are suitable for a group of {req.num_people} people. 
        If not, just provide general transportation options available in the city.
        """
    
    result = extract_with_retry(
        query=query,
        system_prompt=SYSTEM_PROMPT,
        output_schema=TransportationResults,
        is_good_result=lambda r: bool(r.transportation_options) and any(f.type for f in r.transportation_options),
        agent_name="TransportationAgent"
    )

    transportation = [f.model_dump() for f in result.transportation_options] if result else []
    return {"research": {
        "transportation": transportation},
        "failed_agents": state.failed_agents + ([result.agent_name] if not result.success else [])
    }
