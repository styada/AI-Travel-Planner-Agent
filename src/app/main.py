from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from src.agents.SupervisorAgent import travel_graph
from src.models.TripState import TripState

app = FastAPI()


class MessageRequest(BaseModel):
    message: str
    session_id: str


# In-memory session store
# Each session_id maps to a TripState
sessions: dict[str, TripState] = {}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/plan")
async def plan(request: MessageRequest):
    """
    Main endpoint. Each message advances the graph one step.
    The session stores state between messages so the
    collection loop works across multiple turns.
    """
    # Get or create session state
    state = sessions.get(request.session_id, TripState())

    # Add the user's message
    state = TripState(
        **state.model_dump(),
        messages=state.messages + [HumanMessage(content=request.message)]
    )

    try:
        result = travel_graph.invoke(state)
        updated_state = TripState(**result)
        sessions[request.session_id] = updated_state

        # Get the last AI message to return to the user
        ai_messages = [
            m for m in updated_state.messages
            if hasattr(m, "type") and m.type == "ai"
        ]
        last_message = ai_messages[-1].content if ai_messages else "Something went wrong."

        return {
            "response": last_message,
            "final_plan": updated_state.final_plan,
            "research": updated_state.research.model_dump() if updated_state.final_plan else None,
            "budget_breakdown": updated_state.budget_breakdown if updated_state.final_plan else None,
            "done": updated_state.final_plan is not None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a session so the user can start a new trip."""
    sessions.pop(session_id, None)
    return {"status": "cleared"}
