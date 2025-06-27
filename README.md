# AI-Powered Registration System

*AI-powered registration system built with FastAPI, Streamlit, LangGraph, DSPy, Guardrails AI, and MLflow. The system guides users through a structured conversation, collecting registration details while leveraging AI validation to ensure input accuracy.*

## Project Structure

```
/project-root
│── /app                    # FastAPI backend
│── /frontend_streamlit     # Streamlit frontend
│── README.md               # This file
```

## Setup and Run the Application

### Prerequisites

- **Python 3.9+**
- **Docker & Docker Compose**
- **OpenAI API Key** (set in `.env`)

### Option 1: Run Locally

1. **Navigate to the backend directory:**
   ```sh
   cd app
   ```

2. **Create and activate a virtual environment:**
   ```sh
   python -m venv ../.venv
   source ../.venv/bin/activate  # macOS/Linux
   ../.venv/Scripts/activate     # Windows
   ```

3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Start the FastAPI server:**
   ```sh
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **In a new terminal, navigate to the Streamlit directory:**
   ```sh
   cd ../frontend_streamlit
   ```

6. **Run the Streamlit app:**
   ```sh
   streamlit run index.py --server.port=8501
   ```

7. **Access the app:**
   - FastAPI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Streamlit: [http://localhost:8501](http://localhost:8501)

### Option 2: Run with Docker Compose

1. **Navigate to the backend directory:**
   ```sh
   cd app
   ```

2. **Run Docker Compose:**
   ```sh
   docker-compose up --build
   ```

3. **Access the app:**
   - FastAPI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Streamlit: [http://localhost:8501](http://localhost:8501)
   - MLflow: [http://localhost:5000](http://localhost:5000)

4. **Stop the containers:**
   ```sh
   docker-compose down
   ```

## Environment Variables

Create a `.env` file in the project root:

```ini
OPENAI_API_KEY=your-api-key
VALIDATION_ENGINE=chatgpt
MLFLOW_ENABLED=True
MLFLOW_EXPERIMENT_NAME=user_registration_validation_experiment
GRAPH_OUTPUT_DIR=graph_images
```