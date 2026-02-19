import json
import os
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from src.models.TripState import TripState
from src.models.TripRequest import TripRequest
from src.agents.FlightsAgent import flights_agent
from src.agents.HotelsAgent import hotels_agent
from src.agents.RestaurantAgent import restaurants_agent
from src.agents.ActivitiesAgent import activities_agent
from src.agents.EventsAgent import events_agent
from src.agents.TransportationAgent import transportation_agent

"""
SupervisorAgent is responsible for orchestrating the entire trip planning process.
It will call the various research agents (flights, hotels, restaurants, activities, events, transportation)
to gather information based on the user's trip request.
It will also manage the state of the trip planning process and ensure that all necessary information
is collected before moving to the next step.    
"""

# LLMs
_collection_llm = ChatOllama(model=os.getenv("OLLAMA_TEXT_MODEL"), temperature=0)
_synthesis_llm = ChatGoogleGenerativeAI(model=os.getenv("GOOGLE_GEMINI_MODEL"), temperature=0.3)


COLLECTION_PROMPT = """You are a friendly travel planning assistant.
Your job is to collect the following information from the user:
- origin (departure city)
- destination (where they want to go)
- num_people (number of travelers)
- start_date (departure date)
- end_date (return date)
- budget_per_person (total budget per person in USD)
- interests (optional - types of activities they enjoy)

Rules:
- Only ask for fields that are still missing
- Be conversational, not robotic
- If the user gives you multiple pieces of info at once, capture all of them
- Once you have everything, confirm the details back to the user
- Never make up or assume values for missing fields
"""


def collect_info_node(state: TripState) -> dict:
    """
    Extracts trip details from conversation.
    Loops until all required fields are present.
    """
    messages = state.messages

    # Try to extract whatever the user has given us so far
    extraction_response = _collection_llm.invoke([
        SystemMessage(content="""Extract travel details from this conversation.
            Return ONLY valid JSON with these exact keys, use null for missing fields:
            {
                "origin": string or null,
                "destination": string or null,
                "num_people": number or null,
                "start_date": string or null,
                "end_date": string or null,
                "budget_per_person": number or null,
                "interests": string or null
            }"""),
        *messages
    ])

    try:
        raw = extraction_response.content.strip()
        # Strip markdown code blocks if the model adds them
        if "```" in raw:
            raw = raw.split("```")[1].replace("json", "").strip()
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Model didn't return valid JSON — just keep the conversation going
        data = {}

    # Check what's still missing
    required = ["origin", "destination", "num_people", "start_date", "end_date", "budget_per_person"]
    missing = [f for f in required if not data.get(f)]

    if not missing:
        # Everything is here — build the validated TripRequest
        trip_request = TripRequest(
            origin=data["origin"],
            destination=data["destination"],
            num_people=int(data["num_people"]),
            start_date=data["start_date"],
            end_date=data["end_date"],
            budget_per_person=float(data["budget_per_person"]),
            interests=data.get("interests")
        )

        confirm = _collection_llm.invoke([
            SystemMessage(content=COLLECTION_PROMPT),
            *messages,
            HumanMessage(content=f"Confirm these trip details back to the user warmly and tell them you're starting research: {data}")
        ])

        return {
            "trip_request": trip_request,
            "missing_fields": [],
            "next_step": "dispatch",
            "messages": [AIMessage(content=confirm.content)]
        }

    else:
        # Ask for only the missing fields
        response = _collection_llm.invoke([
            SystemMessage(content=COLLECTION_PROMPT),
            *messages,
            HumanMessage(content=f"These fields are still missing: {missing}. Ask the user for them naturally.")
        ])

        return {
            "missing_fields": missing,
            "next_step": "collect_info",
            "messages": [AIMessage(content=response.content)]
        }
        

AGENTS = [
    ("flights_agent", flights_agent),
    ("hotels_agent", hotels_agent),
    ("restaurants_agent", restaurants_agent),
    ("activities_agent", activities_agent),
    ("events_agent", events_agent),
    ("transportation_agent", transportation_agent),
]


def dispatch_node(state: TripState) -> dict:
    research_updates = {}
    failed = []

    for name, agent_fn in AGENTS:
        print(f"Running {name}...")
        result = agent_fn(state)
        research_updates.update(result.get("research", {}))
        failed.extend(result.get("failed_agents", []))

    return {
        "research": research_updates,
        "failed_agents": failed
    }
    
    
SYNTHESIS_PROMPT = """You are a master travel planner creating a final trip itinerary.
You will be given structured research data from multiple specialist agents.
Write a comprehensive, practical, and engaging trip plan.

Structure your response exactly like this:
1. 📋 TRIP OVERVIEW
2. ✈️ FLIGHTS
3. 🏨 WHERE TO STAY
4. 🍽️ DINING GUIDE
5. 🎯 ACTIVITIES & EXCURSIONS
6. 🎉 EVENTS & ENTERTAINMENT
7. 🚌 GETTING AROUND
8. 💰 BUDGET BREAKDOWN
9. 💡 PRO TIPS

Rules:
- Stay within the budget_per_person provided
- If an agent failed and returned no data, explicitly tell the user that section could not be researched rather than making something up
- Be specific — use real names, real prices from the research data
- Budget breakdown must add up and must not exceed budget_per_person
"""


def synthesis_node(state: TripState) -> dict:
    req = state.trip_request
    research = state.research

    # Build context from structured research data
    research_context = f"""
TRIP DETAILS:
- From: {req.origin} to {req.destination}
- Dates: {req.start_date} to {req.end_date}
- Travelers: {req.num_people}
- Budget per person: ${req.budget_per_person}
- Interests: {req.interests or 'not specified'}

FAILED AGENTS (no data available for these):
{state.failed_agents if state.failed_agents else 'None — all agents succeeded'}

FLIGHTS:
{research.flights if research.flights else 'No data'}

HOTELS:
{research.hotels if research.hotels else 'No data'}

RESTAURANTS:
{research.restaurants if research.restaurants else 'No data'}

ACTIVITIES:
{research.activities if research.activities else 'No data'}

EVENTS:
{research.events if research.events else 'No data'}

TRANSPORTATION:
{research.transportation_options if research.transportation_options else 'No data'}
"""

    response = _synthesis_llm.invoke([
        SystemMessage(content=SYNTHESIS_PROMPT),
        HumanMessage(content=research_context)
    ])

    return {
        "final_plan": response.content,
        "next_step": "done",
        "messages": [AIMessage(content=response.content)]
    }

    
def route_after_collection(state: TripState) -> str:
    if state.next_step == "dispatch":
        return "dispatch"
    return "collect_info"

    
def build_graph():
    graph = StateGraph(TripState)

    # Register all nodes
    graph.add_node("collect_info", collect_info_node)
    graph.add_node("dispatch", dispatch_node)
    graph.add_node("synthesis", synthesis_node)

    # Entry point — always start at collect_info
    graph.add_edge(START, "collect_info")

    # After collect_info — conditional routing
    graph.add_conditional_edges(
        "collect_info",          # from this node
        route_after_collection,  # run this function to decide
        {
            "collect_info": "collect_info",  # if it returns "collect_info" → loop back
            "dispatch": "dispatch"           # if it returns "dispatch" → move forward
        }
    )

    # After dispatch — always go to synthesis
    graph.add_edge("dispatch", "synthesis")

    # After synthesis — done
    graph.add_edge("synthesis", END)

    return graph.compile()


# Module level graph instance
travel_graph = build_graph()