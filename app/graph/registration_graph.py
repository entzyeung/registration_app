# Extend BaseGraphManager to handle registration-specific logic, 
# including conditional edges for skipping optional steps (address, phone).
"""
BaseGraphManager creates a linear graph by default, connecting nodes (questions) in sequence.
RegistrationGraphManager overrides _build_graph to add conditional edges, allowing users to skip ask_address and ask_phone.
The generate_mermaid_diagram method visualizes the graph as a PNG, aiding debugging.
"""

from langgraph.graph import END
from db.postgres_db import RegistrationState
from graph.base_graph import BaseGraphManager
import logging


class RegistrationGraphManager(BaseGraphManager):
    """Specialized graph manager with domain-specific (registration) logic."""

    # inherits from BaseGraphManager, meaning it is a subclass that extends the functionality of BaseGraphManager.
    # The super().__init__ call passes 3 variables to the parent class’s constructor during initialization to set up the inherited attributes 
    # (e.g., self.name, self.question_map, self.graph). The parent class uses these to configure the graph.
    def __init__(self, name: str, question_map: dict):
        # We pass RegistrationState as the state_class as it is instantiated.
        super().__init__(name, question_map, RegistrationState)

    def _build_graph(self): # replace this same build_graph in base_graph.py
        """
        Override the base build method to incorporate optional steps,
        or domain-specific edges.(e.g. skip optional steps (ask_address and ask_phone).)
        """

        # Defines a series of nested helper function,
        # e.g. ask_question (replacing _ask_question from the base class).
        def ask_question(state: RegistrationState, question_text: str):
            logging.info(f"[Registration] Transitioning to: {question_text}")
            return {
                "collected_data": state.collected_data,
                "current_question": question_text,
            }

        def create_question_node(question_text):
            # is a placeholder for the state (an instance of RegistrationState) that will be provided when the graph executes.
            return lambda s: ask_question(s, question_text)

        # Add each node
        for key, question_text in self.question_map.items():
            self.graph.add_node(key, create_question_node(question_text))

        # Set entry point, Sets the graph’s entry point to the "ask_email" node, 
        # meaning the graph starts by asking for the user’s email.
        self.graph.set_entry_point("ask_email")

        # Normal edges for the first two nodes
        self.graph.add_edge("ask_email", "ask_name")

        def path_func(state: RegistrationState):
            """Determine where to go next, considering multiple skips."""
            skip_address = state.collected_data.get("skip_ask_address", False)
            skip_phone = state.collected_data.get("skip_ask_phone", False)

            if skip_address and skip_phone:
                return "ask_username"  # Skip both address and phone
            elif skip_address:
                return "ask_phone"  # Skip address only
            else:
                return "ask_address"  # Default to asking for address first

        self.graph.add_conditional_edges(
            source="ask_name",
            path=path_func,
            path_map={
                "ask_address": "ask_address",
                "ask_phone": "ask_phone",
                "ask_username": "ask_username",
            },
        )

        self.graph.add_edge("ask_address", "ask_phone")
        self.graph.add_conditional_edges(
            source="ask_phone",
            path=lambda state: (
                "ask_username"
                if state.collected_data.get("skip_ask_phone", False)
                else "ask_username"
            ),
            path_map={"ask_username": "ask_username"},
        )
        self.graph.add_edge("ask_username", "ask_password")
        self.graph.add_edge("ask_password", END)
