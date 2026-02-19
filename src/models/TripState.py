from typing import Optional
from pydantic import BaseModel, Field
from typing_extensions import Annotated
from langgraph.graph.message import add_messages
from models import ResearchResults, TripRequest


class TripState(BaseModel):
    messages: Annotated[list, add_messages] = Field(default_factory=list)
    trip_request: Optional[TripRequest] = None
    research: ResearchResults = Field(default_factory=ResearchResults)
    missing_fields: list[str] = Field(default_factory=list)
    next_step: str = "collect_info"
    final_plan: Optional[str] = None      # narrative summary for reading
    budget_breakdown: dict = Field(default_factory=dict)  # computed totals

    class Config:
        arbitrary_types_allowed = True