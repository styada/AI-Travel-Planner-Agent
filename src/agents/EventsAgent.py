from pydantic import BaseModel, Field
from models.ResearchResults import EventOption
from models.TripState import TripState
from tools.data_extraction_tool import extract_with_retry


class EventResults(BaseModel):
    events: list[EventOption] = Field(
        description="List of events and entertainment options happening during the trip. Each option includes details such as name, description, date, price, location, duration, booking URL, contact information, and timings."
    )


SYSTEM_PROMPT = """
    You are an events and entertainment research specialist.
    You will be given web search results about events, shows, concerts, and entertainment.
    Extract concrete event options from the results and return them.

    Rules:
    - Only include events with a real name
    - Price must be a number in USD (if available, otherwise 0)
    - If booking URL is not found, leave it null
    - Return at most 5 options
    - Include the event date and timings if available
    - Include a variety of entertainment types (concerts, shows, plays, festivals, etc.)
    - Do not invent events that are not in the search results
"""

def events_agent(state: TripState) -> dict:
    req = state.trip_request
    query = {
        f"""
        Find events and entertainment happening in {req.destination} between {req.start_date} and {req.end_date}.
        Look for concerts, shows, theater performances, festivals, exhibitions, and other entertainment options.
        Include booking URLs, ticket prices, and event timings.
        """
    }
    
    result = extract_with_retry(
        query=query,
        system_prompt=SYSTEM_PROMPT,
        output_schema=EventResults,
        is_good_result=lambda r: bool(r.events) and any(f.location for f in r.events)
    )

    events = [f.model_dump() for f in result.events] if result else []
    return {"research": {"events": events}}
