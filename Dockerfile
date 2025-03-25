# Use a Python base image with gcloud SDK
FROM python:3.9-slim

# Install necessary packages
RUN apt-get update && apt-get install -y \
    curl \
    google-cloud-sdk \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY main.py .

# Set environment variables (adjust as needed)
ENV GOOGLE_CLOUD_PROJECT=<your-project-id>
ENV PUBSUB_TOPIC=<your-pubsub-topic>
ENV PUBSUB_SUBSCRIPTION=<your-pubsub-subscription>

# Authenticate gcloud (using application default credentials)
# This assumes your Cloud Run service account has Pub/Sub permissions.
RUN gcloud auth application-default login --no-launch-browser

# Run the Python script
CMD ["python", "main.py"]