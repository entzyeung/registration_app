FROM python:3.10-slim

# Set working directory in the container
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY index.py .
COPY tab1.txt .

# Expose Streamlit port
EXPOSE 8501

# Health check for Streamlit
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "index.py", "--server.port=8501", "--server.address=0.0.0.0"]