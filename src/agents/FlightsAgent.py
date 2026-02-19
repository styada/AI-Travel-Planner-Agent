import os

from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field
from models.ResearchResults import FlightOption


class FlightResults(BaseModel):
    flights: list[FlightOption] = Field(
        description="List of flight options that match the trip request criteria. Each option includes details such as airline, departure and arrival times, price, origin, destination, duration, booking URL, and class type."
    )
    

_llm = ChatOllama(model=os.getenv("OLLAMA_TEXT_MODEL"))