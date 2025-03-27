FROM python:3.9-slim

# Install required packages
RUN apt-get update && apt-get install -y \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Create SSH directory and set proper permissions
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Expose API port
EXPOSE 8080

# Start the Flask API
CMD ["gunicorn", "-b", "0.0.0.0:8080", "main:app"]
