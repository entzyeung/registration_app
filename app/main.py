from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse  # Added missing import
import uuid
import logging
from app.validation.factory import validate_user_input
from app.db.sqlite_db import fetch_session_from_db, upsert_session_to_db, RegistrationState
from app.graph.registration_graph import RegistrationGraphManager
import pandas as pd
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

logging.basicConfig(level=logging.INFO)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8080",
        "http://localhost:5173",
        "http://localhost:8501",  # Added for Streamlit
        "https://huggingface.co/spaces/Entz/council_3",  # Add your Hugging Face Space URL
        "https://entz-council-3.hf.space",
        "*"# Temporary wildcard for testing
    ],
    allow_credentials=True, # Permits cookies/credentials in requests.
    allow_methods=["*"], # Allows all HTTP methods (GET, POST, etc.).
    allow_headers=["*"], # Allows all headers, ensuring flexibility for front-end apps.
)

registration_questions = {
    "ask_email": "What is your email address?",
    "ask_name": "What is your full name?",
    "ask_address": "What is your address?",
    "ask_phone": "What is your phone number?",
    "ask_username": "Choose a username.",
    "ask_password": "Choose a strong password.",
}

registration_graph = RegistrationGraphManager("registration", registration_questions)
registration_graph.generate_mermaid_diagram()


#####################################################
#################### Endpoints 1 ####################
# Purpose: Initializes a new session, starts the graph at ask_email, saves the state, and returns the first question to the client.
@app.post("/start_registration") # endpoint initializes a new session, 
# assigning a unique session_id and starting the registration flow.
def start_registration():
    session_id = str(uuid.uuid4())

    # Our initial state
    """
    It is basically initial_state={} 
    + type hint RegistrationState.
    """
    initial_state: RegistrationState = {
        "collected_data": {},
        "current_question": "",
        "current_node": "ask_email",
        "session_id": session_id,
    }

    # Start the graph & get the first node
    ############### kick off the graph ###############
    execution = registration_graph.compiled_graph.stream(initial_state)
    try:
        steps = list(execution)  # Fully consume the generator
        if not steps:
            raise RuntimeError("Generator exited before producing any states.")
        first_step = steps[0]
    except GeneratorExit:
        raise RuntimeError("GeneratorExit detected before first transition!")

    # Extract state from the first node
    first_node_key = list(first_step.keys())[0]
    first_node_state = first_step[first_node_key]
    first_node_state["current_node"] = first_node_key
    first_node_state["session_id"] = session_id

    # Save to session
    upsert_session_to_db(
        session_id,
        first_node_state["collected_data"],
        first_node_state["current_question"],
        first_node_state["current_node"],
    )

    return {
        "session_id": session_id,
        "message": first_node_state["current_question"],
        "state": first_node_state,
    }



#####################################################
#################### Endpoints 2 ####################
# This endpoint processes user responses, validates them, updates the state, and advances the graph.

@app.post("/submit_response")
def submit_response(response: dict):
    session_id = response.get("session_id")
    if not session_id:
        return {"error": "Missing session_id"}

    current_state = fetch_session_from_db(session_id)
    if not current_state:
        return {"error": "Session not found. Please restart registration."}

    skip_steps = response.get("skip_steps", [])
    for node_key in skip_steps:
        logging.info(f"skip_{node_key}")
        current_state[f"skip_{node_key}"] = True

    user_answer = response.get("answer", "")
    current_question = current_state["current_question"]
    current_node = current_state["current_node"]

    # Use dspy to validate the answer with fallbacks
    if current_node in skip_steps:
        # If user is skipping this question, create a dummy validation result
        validation_result = {
            "status": "valid",
            "feedback": "Skipped this question",
            "formatted_answer": "-",
        }
        logging.info(f"Skipping validation for {current_node}")
    else:
        # Normal validation
        validation_result = validate_user_input(current_question, user_answer)

        # If there's a clarify/error
        if validation_result["status"] in ("clarify", "error"):
            return {
                "next_question": current_question,
                "validation_feedback": validation_result["feedback"],
                "user_answer": user_answer,
                "formatted_answer": validation_result["formatted_answer"],
                "state": current_state,
            }

    current_state["collected_data"][current_state["current_node"]] = validation_result[
        "formatted_answer"
    ]

    if "current_node" not in current_state or not current_state.get("collected_data"):
        return {"error": "Corrupt session state, restart registration."}

    next_step = registration_graph.resume_and_step_graph(current_state)

    if not next_step or next_step == {}:
        # Means we've hit the END node or no more steps
        return {
            "message": "Registration complete!",
            "validation_feedback": validation_result["feedback"],
            "user_answer": user_answer,
            "formatted_answer": validation_result["formatted_answer"],
            "state": current_state,
            "summary": current_state["collected_data"],
        }

    next_node_key = list(next_step.keys())[0]
    next_node_state = next_step[next_node_key]
    next_node_state["current_node"] = next_node_key

    upsert_session_to_db(
        session_id,
        current_state["collected_data"],
        next_node_state["current_question"],
        next_node_state["current_node"],
    )

    return {
        "next_question": next_node_state["current_question"],
        "validation_feedback": validation_result["feedback"],
        "user_answer": user_answer,
        "formatted_answer": validation_result["formatted_answer"],
        "state": next_node_state,
        "summary": current_state["collected_data"],
    }


#####################################################
#################### Endpoints 3 ####################
@app.post("/edit_field")
def edit_field(request: dict):
    session_id = request.get("session_id")
    if not session_id:
        return {"error": "Missing session_id"}

    field_to_edit = request.get("field_to_edit")
    new_value = request.get("new_value")

    current_state = fetch_session_from_db(session_id)
    if not current_state:
        logging.error("Session not found. Please restart registration.")
        return {"error": "Session not found. Please restart registration."}

    question_text = registration_questions.get(field_to_edit)
    if not question_text:
        logging.error(f"Invalid field_to_edit: {field_to_edit}")
        return {"error": f"Invalid field_to_edit: {field_to_edit}"}

    validation_result = validate_user_input(
        question=question_text, user_answer=new_value
    )

    if validation_result["status"] == "clarify":
        return {
            "message": "Needs clarification",
            "validation_feedback": validation_result["feedback"],
            "raw_answer": new_value,
            "formatted_answer": validation_result["formatted_answer"],
        }

    current_state["collected_data"][field_to_edit] = validation_result[
        "formatted_answer"
    ]

    upsert_session_to_db(
        session_id,
        current_state["collected_data"],
        current_state["current_question"],
        current_state["current_node"],
    )

    return {
        "message": "Field updated successfully!",
        "validation_feedback": validation_result["feedback"],
        "raw_answer": new_value,
        "formatted_answer": validation_result["formatted_answer"],
        "summary": current_state["collected_data"],
    }
