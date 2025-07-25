import os
os.environ["HOME"] = "/tmp"  # Fix for permission issues on platforms like HuggingFace

import streamlit as st
import requests
import time
import random

API_URL = os.getenv("API_URL")

TRANSITION_MESSAGES = [
    "Now we are moving onto question {number}!",
    "Time to switch to question {number}!",
    "Let's proceed with question {number}!",
    "Moving forward to question {number}!",
    "Onward to question {number}!"
]

# Utility to read intro content from file
def read_intro_file(filepath="tab1.txt"):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Intro file not found."

# Reset session state keys
def reset_session_state():
    keys = [
        "session_id", "current_question", "answer", "feedback", "summary",
        "skip_address", "skip_phone", "prev_question", "question_number"
    ]
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]

def start_registration():
    print("Starting registration...")
    try:
        headers = {"Origin": "https://entz-council-3.hf.space"}
        response = requests.post(
            f"{API_URL}/start_registration",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        print("API Response:", data)
        st.session_state.session_id = data["session_id"]
        st.session_state.current_question = data["message"]
        st.session_state.feedback = ""
        st.session_state.summary = None
        st.session_state.answer = ""
        st.session_state.skip_address = False
        st.session_state.skip_phone = False
        st.session_state.prev_question = ""
        st.session_state.question_number = 1
    except requests.RequestException as e:
        print(f"Error starting registration: {e}, Response: {getattr(e.response, 'text', 'No response')}")
        st.error(f"Error starting registration: {e}")

def submit_response():
    if not st.session_state.session_id:
        st.error("No active session. Please start registration.")
        return
    skip_steps = []
    if st.session_state.get("skip_address", False):
        skip_steps.append("ask_address")
    if st.session_state.get("skip_phone", False):
        skip_steps.append("ask_phone")
    payload = {
        "session_id": st.session_state.session_id,
        "answer": st.session_state.answer,
        "skip_steps": skip_steps
    }
    print("Submitting response with payload:", payload)
    try:
        response = requests.post(
            f"{API_URL}/submit_response",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        print("API Response:", data)
        if data.get("message") == "Registration complete!":
            st.session_state.summary = data["summary"]
            st.session_state.current_question = ""
            st.session_state.feedback = "Registration complete!"
            st.session_state.question_number = 1
        else:
            st.session_state.prev_question = st.session_state.current_question
            st.session_state.current_question = data.get("next_question", "")
            st.session_state.feedback = data.get("validation_feedback", "")
            if st.session_state.prev_question != st.session_state.current_question:
                st.session_state.question_number += 1
            st.session_state.answer = ""
        st.session_state.skip_address = False
        st.session_state.skip_phone = False
        st.rerun()
    except requests.RequestException as e:
        print(f"Error submitting response: {e}")
        st.error(f"Error submitting response: {e}")

def edit_field(field, value):
    if not st.session_state.session_id:
        st.error("No active session.")
        return
    payload = {
        "session_id": st.session_state.session_id,
        "field_to_edit": field,
        "new_value": value
    }
    print("Editing field with payload:", payload)
    try:
        response = requests.post(
            f"{API_URL}/edit_field",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        print("API Response:", data)
        st.session_state.feedback = data.get("validation_feedback", "")
        st.session_state.summary = data.get("summary", st.session_state.summary)
        if data.get("message") == "Needs clarification":
            st.error(f"Clarification needed for {field}: {data['validation_feedback']}")
        elif data.get("message") == "Field updated successfully!":
            st.success("Database updated.")
            st.rerun()
    except requests.RequestException as e:
        print(f"Error editing field: {e}")
        st.error(f"Error editing field: {e}")

# Initialize session state if not present
if "session_id" not in st.session_state:
    st.session_state.session_id = None
    st.session_state.current_question = ""
    st.session_state.answer = ""
    st.session_state.feedback = ""
    st.session_state.summary = None
    st.session_state.skip_address = False
    st.session_state.skip_phone = False
    st.session_state.prev_question = ""
    st.session_state.question_number = 1

if st.session_state.session_id is None:
    start_registration()

st.title("AI-Powered Registration System")
st.markdown("*** If 403 or other connection errors, please refresh the page every 1 minute, because the backend server is being spun up. Developed by entzyeung@gmail.com**")

# Create two tabs
tab1, tab2 = st.tabs(["Introduction", "Registration"])

with tab1:
    intro_text = read_intro_file()
    st.markdown(intro_text)

with tab2:
    if st.session_state.summary:
        st.success("Registration Complete!")
        st.subheader("Summary")
        for key, value in st.session_state.summary.items():
            st.write(f"**{key}**: {value}")
            new_value = st.text_input(f"Edit {key}", key=f"edit_{key}")
            if st.button(f"Update {key}", key=f"update_{key}"):
                edit_field(key, new_value)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Next Registration", key="next_reg"):
                reset_session_state()
                start_registration()
                st.rerun()
        with col2:
            if st.button("End Session", key="end_sess"):
                reset_session_state()
                st.success("Session ended. You may close the tab.")
    else:
        if st.session_state.current_question:
            if st.session_state.feedback:
                st.error(st.session_state.feedback)
            if st.session_state.prev_question and st.session_state.prev_question != st.session_state.current_question:
                transition_msg = random.choice(TRANSITION_MESSAGES).format(number=st.session_state.question_number)
                st.info(transition_msg)
                time.sleep(1)
            st.subheader(f"Question {st.session_state.question_number}: {st.session_state.current_question}")

            is_address_question = st.session_state.current_question == "What is your address?"
            is_phone_question = st.session_state.current_question == "What is your phone number?"

            if is_address_question or is_phone_question:
                st.info(
                    f"This question is optional. Check the box to skip, or enter your information below.\n"
                    f"- For address: Include house number (e.g., 123), street name (e.g., High Street), town/city (e.g., London), and postcode (e.g., SW1A 1AA). Example: 123 High Street, London, SW1A 1AA.\n"
                    f"- For phone: Use 10 digits for landlines (e.g., 020 123 4567) or 11 digits for mobiles starting with 07 (e.g., 07700 900 123). Do not use +44 or other region numbers."
                )
                if is_address_question:
                    st.session_state.skip_address = st.checkbox("Skip this question", value=st.session_state.skip_address)
                elif is_phone_question:
                    st.session_state.skip_phone = st.checkbox("Skip this question", value=st.session_state.skip_phone)

            st.session_state.answer = st.text_input(
                "Your Answer",
                value=st.session_state.answer,
                key=f"answer_input_{st.session_state.question_number}"
            )

            if st.button("Submit", key="submit_button"):
                submit_response()
        else:
            st.info("Initializing session, please wait...")
