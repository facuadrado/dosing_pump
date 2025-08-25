# Using lightweight Python
FROM arm64v8/python:3.11-bookworm

# Setting timezone to EST
ENV TZ=America/New_York

# Set working directory
WORKDIR /app

# Install Rpi.GPIO 
RUN apt-get update 

RUN apt-get install -y python3-rpi.gpio

# Install FastAPI and Uvicorn
RUN pip install fastapi uvicorn RPi.GPIO apscheduler

# Copy the app files
COPY ./app.py .

# Expose port 8000 for the FastAPI app
EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
