# AI Travel Planner Agent - Architecture

## System Overview

This document describes the architecture and workflow of the AI Travel Planner Agent system using PlantUML diagrams.

## High-Level Architecture Diagram

```plantuml
@startuml travel_planner_architecture
!theme plain
skinparam backgroundColor #FEFEFE
skinparam componentStyle rectangle

package "Client" {
    actor User
}

package "FastAPI Application" {
    component API as "FastAPI\n/plan endpoint"
    component SessionMgr as "Session Manager\n(In-memory store)"
}

package "LangGraph Orchestration" {
    component Supervisor as "SupervisorAgent\n(Graph Orchestrator)"
    
    component CollectNode as "collect_info_node\n(Information Collection)"
    component DispatchNode as "dispatch_node\n(Agent Dispatcher)"
    component SynthesisNode as "synthesis_node\n(Trip Plan Synthesis)"
}

package "Research Agents" {
    component FlightsAgent
    component HotelsAgent
    component RestaurantsAgent
    component ActivitiesAgent
    component EventsAgent
    component TransportationAgent
}

package "Tools & Services" {
    component WebSearch as "web_search_tool\n(DuckDuckGo)"
    component DataExtraction as "extract_with_retry\n(Structured Extraction)"
}

package "Language Models" {
    component GoogleGemini as "Google Gemini\n(LLM Provider)"
}

package "External Services" {
    component DuckDuckGo as "DuckDuckGo Search API"
}

User --> API : "POST /plan"
API --> SessionMgr : "Get/Create Session"
API --> Supervisor : "Invoke Graph"

Supervisor --> CollectNode : "Collect Trip Details"
Supervisor --> DispatchNode : "Dispatch Agents"
Supervisor --> SynthesisNode : "Synthesize Plan"

DispatchNode --> FlightsAgent
DispatchNode --> HotelsAgent
DispatchNode --> RestaurantsAgent
DispatchNode --> ActivitiesAgent
DispatchNode --> EventsAgent
DispatchNode --> TransportationAgent

FlightsAgent --> DataExtraction
HotelsAgent --> DataExtraction
RestaurantsAgent --> DataExtraction
ActivitiesAgent --> DataExtraction
EventsAgent --> DataExtraction
TransportationAgent --> DataExtraction

DataExtraction --> WebSearch
DataExtraction --> GoogleGemini

WebSearch --> DuckDuckGo : "Web Search"
GoogleGemini --> GoogleGemini : "Extract Structured Data"

SynthesisNode --> GoogleGemini : "Generate Plan"

Supervisor --> API : "Final State"
SessionMgr --> API : "Store Updated State"
API --> User : "JSON Response"

@enduml
```

## Sequence Diagram - Trip Planning Flow

```plantuml
@startuml travel_planner_sequence
!theme plain
skinparam backgroundColor #FEFEFE
actor User
participant "FastAPI\nAPI" as API
participant "Session\nManager" as Session
participant "Graph\nOrchestrator" as Graph
participant "Collection\nNode" as Collect
participant "Dispatch\nNode" as Dispatch
participant "Research\nAgents" as Agents
participant "Data\nExtraction" as Extract
participant "LLM\n(Gemini)" as LLM
participant "Web\nSearch" as Search
participant "Synthesis\nNode" as Synthesis

User ->> API: POST /plan\n{message, session_id}
activate API

API ->> Session: Get or create session
activate Session
Session -->> API: TripState
deactivate Session

API ->> Graph: Invoke graph with state
activate Graph

Graph ->> Collect: collect_info_node()
activate Collect

Collect ->> LLM: Extract trip details from conversation
activate LLM
LLM -->> Collect: Extracted JSON\n{origin, destination, dates, budget, etc}
deactivate LLM

alt All required fields present
    Collect ->> LLM: Generate confirmation message
    activate LLM
    LLM -->> Collect: Confirmation text
    deactivate LLM
    Collect -->> Graph: next_step = "dispatch"
else Missing fields
    Collect ->> LLM: Ask for missing information
    activate LLM
    LLM -->> Collect: Question text
    deactivate LLM
    Collect -->> Graph: next_step = "collect_info"
end
deactivate Collect

Graph ->> Dispatch: dispatch_node()
activate Dispatch

par Research Agents Run in Parallel
    Dispatch ->> Agents: Call flights_agent
    Dispatch ->> Agents: Call hotels_agent
    Dispatch ->> Agents: Call restaurants_agent
    Dispatch ->> Agents: Call activities_agent
    Dispatch ->> Agents: Call events_agent
    Dispatch ->> Agents: Call transportation_agent
    
    activate Agents
    loop For each agent
        Agents ->> Extract: extract_with_retry(agent_name)
        activate Extract
        
        loop Retry up to 3 times
            Extract ->> Search: web_search_tool(query)
            activate Search
            Search -->> Extract: Raw search results
            deactivate Search
            
            Extract ->> LLM: Extract structured data from results
            activate LLM
            LLM -->> Extract: Structured JSON response
            deactivate LLM
            
            Extract ->> Extract: Validate is_good_result()
            
            alt Results are good
                Extract -->> Agents: AgentResult(success=True)
            else Results are weak or error
                Extract ->> LLM: Generate improved query
                activate LLM
                LLM -->> Extract: Refined query
                deactivate LLM
            end
        end
        deactivate Extract
    end
    deactivate Agents
end

Dispatch -->> Graph: {research_updates, failed_agents}
deactivate Dispatch

Graph ->> Synthesis: synthesis_node()
activate Synthesis

Synthesis ->> LLM: Generate comprehensive trip plan\n(using all research data)
activate LLM
LLM -->> Synthesis: Complete itinerary text
deactivate LLM

Synthesis -->> Graph: {final_plan, next_step = "done"}
deactivate Synthesis

Graph -->> API: Updated TripState
deactivate Graph

API ->> Session: Store updated state
activate Session
Session -->> API: Stored
deactivate Session

API -->> User: {response, final_plan, research, done}
deactivate API

@enduml
```

## Component Responsibilities

### Core Components

| Component | Responsibility |
|-----------|-----------------|
| **FastAPI Application** | HTTP endpoint handling, session management, request/response serialization |
| **SupervisorAgent** | Graph orchestration, state management, node routing |
| **collect_info_node** | Extract and validate trip requirements from conversation |
| **dispatch_node** | Launch and manage research agent execution |
| **synthesis_node** | Generate final trip itinerary from research data |

### Research Agents

Each agent follows the same pattern:
1. Create search query from trip request
2. Call `extract_with_retry()` with agent-specific extraction rules
3. Return structured data

| Agent | Searches For |
|-------|-------------|
| **FlightsAgent** | Flight options, airlines, prices, schedules |
| **HotelsAgent** | Accommodation options, ratings, amenities, prices |
| **RestaurantsAgent** | Restaurant recommendations, cuisine, prices, reservations |
| **ActivitiesAgent** | Tourist attractions, tours, activities, pricing |
| **EventsAgent** | Entertainment, concerts, shows, festivals |
| **TransportationAgent** | Local transit, taxis, rideshare, public transportation |

### Tools & Services

| Tool | Purpose |
|------|---------|
| **web_search_tool** | DuckDuckGo web search for information gathering |
| **extract_with_retry** | LLM-based structured data extraction with automatic query refinement |
| **Google Gemini LLM** | Information collection, data extraction, and trip plan synthesis |

## Data Flow

### State Model (TripState)

```
TripState {
    messages: List[Message]                    # Conversation history
    trip_request: Optional[TripRequest]        # Validated user requirements
    research: ResearchResults                  # Aggregated research data
    missing_fields: List[str]                  # Fields still needed
    next_step: str                             # Graph routing: "collect_info", "dispatch", "done"
    final_plan: Optional[str]                  # Synthesized trip itinerary
    budget_breakdown: dict                     # Cost allocation
    failed_agents: List[str]                   # Agents that couldn't find data
}
```

### TripRequest (Validated)

```
TripRequest {
    origin: str
    destination: str
    num_people: int
    start_date: str
    end_date: str
    budget_per_person: float
    interests: Optional[str]
}
```

### ResearchResults (Aggregated)

```
ResearchResults {
    flights: List[FlightOption]
    hotels: List[HotelOption]
    restaurants: List[RestaurantOption]
    activities: List[ActivityOption]
    events: List[EventOption]
    transportation_options: List[TransportationOption]
}
```

## Error Handling & Resilience

- **Extraction Retries**: Each agent tries up to 3 times with query refinement
- **Failed Agent Tracking**: Failed agents are logged and excluded from synthesis
- **Graceful Degradation**: Synthesis notes missing data rather than failing
- **Session Persistence**: State maintained across multiple user messages

## Logging & Visibility

The system provides comprehensive logging at INFO and DEBUG levels:
- **INFO**: Major node transitions, agent launches, result counts
- **DEBUG**: LLM invocations, query refinements, search results
- **ERROR**: Failures with full exception traces

## Scalability Considerations

1. **Parallel Agent Execution**: Research agents run concurrently via LangGraph
2. **Session-based State**: Each user session is independent and isolated
3. **Lazy LLM Loading**: LLMs instantiated only when needed
4. **Configurable Retries**: Extraction retry count and backoff strategies

