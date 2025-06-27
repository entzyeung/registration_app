from langgraph.graph import StateGraph # creating stateful graph-based workflows.
from langgraph.graph import END

from helpers.config import GRAPH_OUTPUT_DIR
import logging
import os


class BaseGraphManager:
    """A generic graph manager that builds and runs a state machine from a question map."""

    def __init__(self, name: str, question_map: dict, state_class):
        """
        :param name: Unique name for the graph.
        :param question_map: A dictionary mapping node keys to question text (or other config).
        :param state_class: The class to store the graph's state (e.g., RegistrationState).
        """
        self.name = name
        self.question_map = question_map # define nodes and their associated 
        """question_map = {
            "name": "What is your full name?",
            "email": "What is your email address?",
            "age": "How old are you?",
            "confirm": "Please confirm your details."
        }"""
        self.state_class = state_class # an instance

        # graph stores the "state" dict
        self.graph = StateGraph(state_class) # instance manages the state transitions with state_class and stores it in self.graph.
        self._build_graph()
        self.compiled_graph = self.graph.compile() # Compiles the graph into an executable form and stores it in self.compiled_graph

    # This updates the state with the current question while preserving existing collected data.
    # state = current stage of the graph, an instance of state_class
    # question_text = The question text associated with the current node.
    def _ask_question(self, state, question_text: str):
        """Helper function for node logic."""
        logging.info(f"[{self.name}] Transitioning to: {question_text}")
        return {
            "collected_data": getattr(state, "collected_data", {}), # <---- get the state
            # Purpose: Retrieves the collected_data attribute from the state object. 
            # If the attribute doesn’t exist, it returns an empty dictionary {}.
            ### why not state.collected_data? coz getattr handles no value error with {}.
            # when is state updated? when this ask_question function is called, the state is updated in the Ram.
            # when is state persisted? when the "postgres_db.py/upsert_session_to_db" get called.

            "current_question": question_text,
        }

    def _build_graph(self): # will be overrode by RegistrationGraphManager later in registration_graph.py
        """
        A generic build process that:
          1) Creates a node for each item in question_map
          2) Sets a linear path from start to end
        Subclasses can override or extend this method.
        """
        # Create nodes
        for key, question_text in self.question_map.items():
            self.graph.add_node(
                # The node’s logic is defined by a lambda function that 
                # calls _ask_question with the current state (s)
                key, lambda s, q=question_text: self._ask_question(s, q) ######################
            )

        # Set entry point
        nodes = list(self.question_map.keys()) # define the order of nodes.
        self.graph.set_entry_point(nodes[0])  # first item on the node list as the First question

        # Linear path from first to last, then END
        for i in range(len(nodes) - 1):
            self.graph.add_edge(nodes[i], nodes[i + 1])
        self.graph.add_edge(nodes[-1], END)
        # no all the nodes including the end node is architected.



    def resume_and_step_graph(self, state: dict): # < --- state is a dict
        """Resumes the graph from the current node and advances exactly one step."""
        current_node = state.get("current_node") # takes the state dict
        """state is likely a db:
        ...return {
            "session_id": session_id,
            "collected_data": collected_data,
            "current_question": current_question,
            "current_node": current_node, # <------------ hints above
        }
        """
        execution = self.compiled_graph.stream(state) # Creates a stream (iterator) 
        # for executing the compiled graph starting from the provided state.

        logging.info(f"[{self.name}] Resuming graph at: {current_node}")

        if not current_node:
            # Start from the beginning
            try:
                return next(execution)
            except StopIteration: # (indicating the graph is complete)
                logging.info(f"[{self.name}] Graph execution completed.")
                return None

        # Advance until we find current_node, then yield one more step
        for step in execution:
            node_key = list(step.keys())[0]
            if node_key == current_node:
                try:
                    return next(execution)
                except StopIteration:
                    return None
        return None

    def generate_mermaid_diagram(self, filename="graph.png"):
        """Generate a Mermaid diagram PNG from the compiled LangGraph."""

        os.makedirs(GRAPH_OUTPUT_DIR, exist_ok=True)

        # Get the Mermaid code from the compiled graph
        png_data = self.compiled_graph.get_graph().draw_mermaid_png()

        # Save the Mermaid code to a temporary file
        # Define file path
        png_file = os.path.join(GRAPH_OUTPUT_DIR, filename)

        # Save PNG file
        with open(png_file, "wb") as f:  # "wb" for writing binary files
            f.write(png_data)

        logging.info(f"Graph saved at: {png_file}")
        return png_file
