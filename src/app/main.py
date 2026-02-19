import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables first
load_dotenv()

from src.agents.SupervisorAgent import travel_graph
from src.models.TripState import TripState

logger.info("Application started - all modules loaded successfully")

app = FastAPI()


class MessageRequest(BaseModel):
    message: str
    session_id: str


# In-memory session store
# Each session_id maps to a TripState
sessions: dict[str, TripState] = {}


@app.get("/health")
async def health():
    logger.debug("Health check requested")
    return {"status": "ok"}


@app.post("/plan")
async def plan(request: MessageRequest):
    logger.info(f"New request received - Session: {request.session_id}, Message: {request.message[:100]}...")
    
    # Get existing session or create fresh state
    state = sessions.get(request.session_id, TripState())
    if request.session_id in sessions:
        logger.info(f"Resuming existing session: {request.session_id}")
    else:
        logger.info(f"Creating new session: {request.session_id}")

    # Add the user's message to existing state
    state = state.model_copy(update={
        "messages": state.messages + [HumanMessage(content=request.message)]
    })
    logger.debug(f"Message added to state. Total messages: {len(state.messages)}")

    try:
        logger.info(f"Invoking travel graph for session {request.session_id}")
        result = travel_graph.invoke(state)
        updated_state = TripState(**result)
        sessions[request.session_id] = updated_state
        logger.info(f"Travel graph completed successfully for session {request.session_id}")
        logger.debug(f"Updated state - Next step: {updated_state.next_step}, Missing fields: {updated_state.missing_fields}")

        # Get the last AI message to return to the user
        ai_messages = [
            m for m in updated_state.messages
            if hasattr(m, "type") and m.type == "ai"
        ]
        last_message = ai_messages[-1].content if ai_messages else "Something went wrong."

        response = {
            "response": last_message,
            "final_plan": updated_state.final_plan,
            "research": updated_state.research.model_dump() if updated_state.final_plan else None,
            "budget_breakdown": updated_state.budget_breakdown if updated_state.final_plan else None,
            "done": updated_state.final_plan is not None
        }
        logger.info(f"Response prepared for session {request.session_id} - Plan complete: {response['done']}")
        return response

    except Exception as e:
        logger.error(f"Error processing request for session {request.session_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a session so the user can start a new trip."""
    logger.info(f"Clearing session: {session_id}")
    sessions.pop(session_id, None)
    logger.debug(f"Session {session_id} cleared")
    return {"status": "cleared"}
