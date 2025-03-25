# Use an official Python runtime as base
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install Git and any necessary dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY main.py requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the application's port
EXPOSE 8080

# Command to run the application
CMD ["gunicorn", "-b", "0.0.0.0:8080", "main:app"]
