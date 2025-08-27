# Using lightweight Python
FROM arm64v8/python:3.11-bookworm

# Setting timezone to EST
ENV TZ=America/New_York

# Set working directory
WORKDIR /app

# Install Rpi.GPIO 
RUN apt-get update && apt-get install -y python3-rpi.gpio

# Copy files to the container
COPY . /app

# Installing application
RUN pip install .

# Expose port 8000 for the FastAPI app
EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
