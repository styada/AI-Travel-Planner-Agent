from pydantic import BaseModel, Field
from models.ResearchResults import ActivityOption
from models.TripState import TripState
from tools.data_extraction_tool import extract_with_retry


class ActivityResults(BaseModel):
    activities: list[ActivityOption] = Field(
        description="List of activities and attractions in the destination. Each option includes details such as name, description, price, location, duration, booking URL, contact information, and operating timings."
    )


SYSTEM_PROMPT = """
    You are an activities and attractions research specialist.
    You will be given web search results about activities, tours, and attractions.
    Extract concrete activity options from the results and return them.

    Rules:
    - Only include activities with a real name
    - Price must be a number in USD (if available, otherwise 0)
    - If booking URL is not found, leave it null
    - Return at most 5 options
    - Include duration in hours if available
    - Provide a diverse mix of activities (museums, tours, outdoor activities, cultural sites, etc.)
    - Include operating hours and contact information if available
    - Do not invent activities that are not in the search results
"""

def activities_agent(state: TripState) -> dict:
    req = state.trip_request
    query = {
        f"""
        Find popular activities, tours, and attractions in {req.destination} suitable for a group of {req.group_size} people.
        Include museums, historical sites, outdoor activities, guided tours, adventure activities, and cultural experiences.
        Include pricing, duration, booking URLs, and operating hours.
        """
    }
    
    result = extract_with_retry(
        query=query,
        system_prompt=SYSTEM_PROMPT,
        output_schema=ActivityResults,
        is_good_result=lambda r: bool(r.activities) and any(f.location for f in r.activities)
    )

    activities = [f.model_dump() for f in result.activities] if result else []
    return {"research": {"activities": activities}}
