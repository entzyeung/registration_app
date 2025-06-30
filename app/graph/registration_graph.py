from langgraph.graph import END
from app.db.sqlite_db import RegistrationState
from app.graph.base_graph import BaseGraphManager
import logging


class RegistrationGraphManager(BaseGraphManager):
    """Specialized graph manager with domain-specific (registration) logic."""

    def __init__(self, name: str, question_map: dict):
        super().__init__(name, question_map, RegistrationState)

    def _build_graph(self):
        """
        Override the base build method to incorporate optional steps,
        or domain-specific edges.(e.g. skip optional steps (ask_address and ask_phone).)
        """

        def ask_question(state: RegistrationState, question_text: str):
            logging.info(f"[Registration] Transitioning to: {question_text}")
            return {
                "collected_data": state.collected_data,
                "current_question": question_text,
            }

        def create_question_node(question_text):
            return lambda s: ask_question(s, question_text)

        for key, question_text in self.question_map.items():
            self.graph.add_node(key, create_question_node(question_text))

        self.graph.set_entry_point("ask_email")

        self.graph.add_edge("ask_email", "ask_name")

        def path_func(state: RegistrationState):
            """Determine where to go next, considering multiple skips."""
            skip_address = state.collected_data.get("skip_ask_address", False)
            skip_phone = state.collected_data.get("skip_ask_phone", False)

            if skip_address and skip_phone:
                return "ask_username"  
            elif skip_address:
                return "ask_phone"  
            else:
                return "ask_address"  

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
