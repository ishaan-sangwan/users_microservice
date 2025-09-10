FROM python:3.10-slim

LABEL authors="j1roscope"

# Set working directory
WORKDIR /app

# Copy code and requirements
COPY src/ .
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8000

# Run FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
