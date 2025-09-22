# Use Python base image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies including ffmpeg
RUN apt-get update && apt-get install -y ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Expose a dummy port (7860 works fine)
EXPOSE 7860

# Start app (uses Railway $PORT automatically at runtime)
CMD ["python", "app.py"]
