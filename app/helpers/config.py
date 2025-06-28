import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # gpt-4.1-mini
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key. Set the OPENAI_API_KEY environment variable.")
VALIDATION_ENGINE = os.getenv("VALIDATION_ENGINE", "dspy") # chatgpt or dspy
MLFLOW_ENABLED = os.getenv("MLFLOW_ENABLED", "False").lower() in ("true", "1")
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "DefaultExperiment")
GRAPH_OUTPUT_DIR = os.getenv("GRAPH_OUTPUT_DIR", "/tmp/LangGraph_Output")

