# Use an official Python runtime as base
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install Git, OpenSSH, and dependencies
RUN apt-get update && apt-get install -y git openssh-client && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY main.py requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create SSH directory and set correct permissions
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh

# Copy the SSH private key (will be mounted as a secret in Cloud Run)
COPY id_rsa /root/.ssh/id_rsa
RUN chmod 600 /root/.ssh/id_rsa

# Add GitHub to known hosts to prevent SSH fingerprint prompt
RUN ssh-keyscan github.com >> /root/.ssh/known_hosts

# Expose the application's port
EXPOSE 8080

# Command to run the application
CMD ["gunicorn", "-b", "0.0.0.0:8080", "main:app"]
