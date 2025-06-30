from langgraph.graph import StateGraph # creating stateful graph-based workflows.
from langgraph.graph import END

from app.helpers.config import GRAPH_OUTPUT_DIR
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
        self.question_map = question_map # 
        """question_map = {
            "name": "What is your full name?",
            "email": "What is your email address?",
            "age": "How old are you?",
            "confirm": "Please confirm your details."
        }"""
        self.state_class = state_class 

     
        self.graph = StateGraph(state_class) 
        self._build_graph()
        self.compiled_graph = self.graph.compile() 


    def _ask_question(self, state, question_text: str):
        """Helper function for node logic."""
        logging.info(f"[{self.name}] Transitioning to: {question_text}")
        return {
            "collected_data": getattr(state, "collected_data", {}), 
            "current_question": question_text,
        }

    def _build_graph(self):
        """
        A generic build process that:
          1) Creates a node for each item in question_map
          2) Sets a linear path from start to end
        Subclasses can override or extend this method.
        """
        # Create nodes
        for key, question_text in self.question_map.items():
            self.graph.add_node(
                key, lambda s, q=question_text: self._ask_question(s, q) 
            )

        nodes = list(self.question_map.keys()) 
        self.graph.set_entry_point(nodes[0])

        for i in range(len(nodes) - 1):
            self.graph.add_edge(nodes[i], nodes[i + 1])
        self.graph.add_edge(nodes[-1], END)




    def resume_and_step_graph(self, state: dict): 
        """Resumes the graph from the current node and advances exactly one step."""
        current_node = state.get("current_node")
        """state is likely a db:
        ...return {
            "session_id": session_id,
            "collected_data": collected_data,
            "current_question": current_question,
            "current_node": current_node, # <------------ hints above
        }
        """
        execution = self.compiled_graph.stream(state) 


        logging.info(f"[{self.name}] Resuming graph at: {current_node}")

        if not current_node:

            try:
                return next(execution)
            except StopIteration: 
                logging.info(f"[{self.name}] Graph execution completed.")
                return None

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

        png_data = self.compiled_graph.get_graph().draw_mermaid_png()


        png_file = os.path.join(GRAPH_OUTPUT_DIR, filename)


        with open(png_file, "wb") as f:  
            f.write(png_data)

        logging.info(f"Graph saved at: {png_file}")
        return png_file
