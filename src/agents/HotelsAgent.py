from pydantic import BaseModel, Field
from models.ResearchResults import HotelOption
from models.TripState import TripState
from tools.data_extraction_tool import extract_with_retry


class HotelResults(BaseModel):
    hotels: list[HotelOption] = Field(
        description="List of hotel options that match the trip request criteria. Each option includes details such as name, location, price per night, rating, amenities, booking URL, neighborhood description, contact information, and reviews."
    )


SYSTEM_PROMPT = """
    You are an accommodation research specialist.
    You will be given web search results about hotels and accommodations.
    Extract concrete options from the results and return them.

    Rules:
    - Only include accommodations with a real name
    - Price must be a number in USD
    - If booking URL is not found, leave it null
    - Return at most 5 options
    - Include a brief description of the neighborhood if available, as well as any contact information and reviews you can find
    - Include a range of accommodation types such as hotels, hostels, and Airbnbs if available
    - Include amenities if available
    - Do not invent hotels that are not in the search results
"""

def hotels_agent(state: TripState) -> dict:
    req = state.trip_request
    query = f"""
        Find accommodations in {req.destination}. Look for Hotels, well-rated hostels, and Airbnbs that are available around {req.start_date} to {req.end_date}.
        show a range of prices and options, and include booking URLs if available.
        """
    
    result = extract_with_retry(
        query=query,
        system_prompt=SYSTEM_PROMPT,
        output_schema=HotelResults,
        is_good_result=lambda r: bool(r.hotels) and any(f.price > 0 for f in r.hotels),
        agent_name="HotelsAgent"
    )

    hotels = [f.model_dump() for f in result.hotels] if result else []
    return {"research": {
        "hotels": hotels},
        "failed_agents": state.failed_agents + ([result.agent_name] if not result.success else [])
    }