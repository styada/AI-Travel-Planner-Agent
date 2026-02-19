import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field
from models.ResearchResults import HotelOption
from models.TripState import TripState
from tools.web_search_tool import web_search_tool


class HotelResults(BaseModel):
    hotels: list[HotelOption] = Field(
        description="List of hotel options that match the trip request criteria. Each option includes details such as name, location, price per night, rating, amenities, booking URL, neighborhood description, contact information, and reviews."
    )
    

_llm = ChatOllama(model=os.getenv("OLLAMA_TEXT_MODEL"), temperature=0)

_structured_llm = _llm.with_structured_output(HotelResults) # Super fucking cool btw

SYSTEM_PROMPT = """
    You will be given raw web search results about hotels and accommodations.
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
    
    query = {
        f"""
        Find accommodations in {req.destination}. Look for Hotels, well-rated hostels, and Airbnbs that are available around {req.start_date} to {req.end_date}.
        show a range of prices and options, and include booking URLs if available.
        """
    }
    
    raw_response = web_search_tool(query)
    
    structured_response: HotelResults = _structured_llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Extract accommodation options from these search results:\n\n{raw_response}")
    ])
    
    return{
        "research": {
            "hotels": [f.model_dump() for f in structured_response.hotels]
        }
    }