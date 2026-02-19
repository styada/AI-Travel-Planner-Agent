from typing import Optional
from pydantic import BaseModel


class ActivityOption(BaseModel):
    name: str
    description: Optional[str] = None  # There may not always be a description available
    price: float = 0.0 # Default to 0 if price is not provided
    location: Optional[str] = None
    duration: Optional[float] = None  # Duration in hours, optional as it may not always be provided
    booking_url: Optional[str] = None  # URL for booking the activity, optional as it may not always be provided
    contact_info: Optional[str] = None  # Contact information for the activity provider, optional as it may not always be provided
    timings: Optional[str] = None  # Timings for the activity, optional as it may not always be provided

    
class EventOption(BaseModel):
    name: str
    description: Optional[str] = None  # There may not always be a description available
    date: Optional[str] = None  # Date of the event, optional as event could be a week long
    price: float = 0.0 # Default to 0 if price is not provided
    location: Optional[str] = None
    duration: Optional[float] = None  # Duration in hours, optional as it may not always be provided
    booking_url: Optional[str] = None  # URL for booking the activity, optional as it may not always be provided
    contact_info: Optional[str] = None  # Contact information for the activity provider, optional as it may not always be provided
    timings: Optional[str] = None  # Timings for the activity, optional as it may not always be provided

    
class FlightOption(BaseModel):
    airline: str
    departure_time: str
    arrival_time: str
    price: float
    origin: str
    destination: str
    duration: Optional[str] = None
    booking_url: Optional[str] = None
    class_type: Optional[str] = "Economy"  # Economy, Business, First Class, etc. Optional as it may not always be provided

    
class HotelOption(BaseModel):
    name: str
    location: str
    price_per_night: float
    rating: Optional[float] = None
    amenities: Optional[list] = None
    booking_url: Optional[str] = None
    neighborhood: Optional[str] = None  # Description of the neighborhood where the hotel is located, optional as it may not always be provided
    contact_info: Optional[str] = None  # Contact information for the hotel, optional as it may not always be provided
    reviews: Optional[list] = None  # List of reviews for the hotel, optional as it may not always be provided


class RestaurantOption(BaseModel):
    name: str
    cuisine: Optional[str] = None
    price_range: Optional[str] = None
    location: Optional[str] = None
    rating: Optional[float] = None
    reservation_url: Optional[str] = None
    contact_info: Optional[str] = None  # Contact information for the restaurant, optional
    opening_hours: Optional[str] = None  # Opening hours for the restaurant, optional as it may not always be provided
    reviews: Optional[list] = None  # List of reviews for the restaurant, optional as
    recommended_menu: Optional[list] = None  # Menu items for the restaurant, optional as it may not always be provided
    closing_hours: Optional[str] = None  # Closing hours for the restaurant, optional as it may not always be provided
    
    
class TransportationOption(BaseModel):
    type: str # Train, Bus, Metro, Taxi, Rideshare, etc
    price: Optional[float] = None
    duration: Optional[str] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    booking_url: Optional[str] = None
    contact_info: Optional[str] = None  # Contact information for the transportation provider, optional
    class_type: Optional[str] = None  # Economy, Business, First Class, etc


class ResearchResults(BaseModel):
    flights: list[FlightOption] = []
    hotels: list[HotelOption] = []
    restaurants: list[RestaurantOption] = []
    activities: list[ActivityOption] = []
    events: list[EventOption] = []
    transportation_options: list[TransportationOption] = []