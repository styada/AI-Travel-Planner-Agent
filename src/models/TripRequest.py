from typing import Optional
from pydantic.v1 import BaseModel


class TripRequest(BaseModel):
    origin: str
    destination: str
    num_people: int
    start_date: str
    end_date: str
    budget_per_person: float
    interests: Optional[str] = None