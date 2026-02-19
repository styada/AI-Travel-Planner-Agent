from pydantic import BaseModel, Field
from models.ResearchResults import RestaurantOption
from models.TripState import TripState
from tools.data_extraction_tool import extract_with_retry


class RestaurantResults(BaseModel):
    restaurants: list[RestaurantOption] = Field(
        description="List of restaurant options in the destination. Each option includes details such as name, cuisine type, price range, location, rating, reservation URL, contact information, opening hours, reviews, and recommended menu items."
    )


SYSTEM_PROMPT = """
    You are a restaurant research specialist.
    You will be given web search results about restaurants and dining options.
    Extract concrete restaurant options from the results and return them.

    Rules:
    - Only include restaurants with a real name
    - Price range should be documented (e.g., "$$", "$$$", "$$$$")
    - If reservation URL is not found, leave it null
    - Return at most 5 options
    - Include a range of cuisine types and price points if available
    - Include ratings, reviews, opening hours, and recommended dishes if available
    - Do not invent restaurants that are not in the search results
"""

def restaurants_agent(state: TripState) -> dict:
    req = state.trip_request
    query = {
        f"""
        Find highly-rated restaurants in {req.destination}.
        Look for a variety of cuisine types and price ranges suitable for a group of {req.group_size} people.
        Include upscale dining, casual restaurants, and local favorites.
        Include reservation URLs if available, and recommended dishes.
        """
    }
    
    result = extract_with_retry(
        query=query,
        system_prompt=SYSTEM_PROMPT,
        output_schema=RestaurantResults,
        is_good_result=lambda r: bool(r.restaurants) and any(f.location for f in r.restaurants)
    )

    restaurants = [f.model_dump() for f in result.restaurants] if result else []
    return {"research": {"restaurants": restaurants}}
