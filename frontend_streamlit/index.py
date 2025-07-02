import streamlit as st
import requests
import json
import time
import random
import os



API_URL = os.getenv("API_URL")

TRANSITION_MESSAGES = [
    "Now we are moving onto question {number}!",
    "Time to switch to question {number}!",
    "Let's proceed with question {number}!",
    "Moving forward to question {number}!",
    "Onward to question {number}!"
]

def start_registration():
    print("Starting registration...")
    try:
        headers = {"Origin": "https://entz-council-3.hf.space"}
        response = requests.post(f"{API_URL}/start_registration", headers=headers, timeout=10)
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
        response = requests.post(f"{API_URL}/submit_response", json=payload)
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
        response = requests.post(f"{API_URL}/edit_field", json=payload)
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

if "session_state" not in st.session_state:
    st.session_state.session_state = {}
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

# Read content from text files
def read_content_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        return f"Error: {file_path} not found."

st.title("AI-Powered Registration System")
st.markdown("**Developed by entzyeung@gmail.com**")

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
        if st.button("Next Registration", key="next_reg", on_click=start_registration):
            pass
    with col2:
        if st.button("End Session", key="end_sess", on_click=start_registration):
            pass
else:
    if st.session_state.current_question:
        if st.session_state.feedback:
            st.error(st.session_state.feedback)
        if st.session_state.prev_question and st.session_state.prev_question != st.session_state.current_question:
            transition_msg = random.choice(TRANSITION_MESSAGES).format(number=st.session_state.question_number)
            st.info(transition_msg)
            time.sleep(1)
        print(f"Displaying question: {st.session_state.current_question}")
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

        st.components.v1.html("""
            document.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && document.activeElement.tagName === 'INPUT') {
                    e.preventDefault();
                    const submitButton = document.querySelector('button[key="submit_button"]');
                    if (submitButton && !submitButton.disabled) submitButton.click();
                }
            });
        """, height=0)

        st.session_state.answer = st.text_input("Your Answer", value="", key=f"answer_input_{st.session_state.question_number}")

        if st.button("Submit", key="submit_button"):
            submit_response()
    else:
        print("Waiting for session to initialize...")