# Use Python base image
FROM python:3.13-bullseye

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

# Expose port 8080 (Railway default inside container)
EXPOSE 8080

# Start app using env variable
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
