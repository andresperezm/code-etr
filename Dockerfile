FROM python:3.13.2 AS builder

ARG CODE_ETR_VERSION=0.12.1

WORKDIR /build

COPY code_etr_${CODE_ETR_VERSION}.tar.bz2 .

RUN tar -xjvf code_etr_${CODE_ETR_VERSION}.tar.bz2 && \
    rm code_etr_${CODE_ETR_VERSION}.tar.bz2 && \
    cd code_etr && \
    python3 -m venv ./.venv && \
    chmod +x ./.venv/bin/activate && \
    ./.venv/bin/activate && \
    python3 -m pip install lib/code_etr-${CODE_ETR_VERSION}-py3-none-any.whl && \
    pip install pyinstaller && \
    pyinstaller --onefile bin/code_etr

FROM python:3.13.2  AS final

WORKDIR /app

RUN mkdir -p /tmp/config && chmod 700 /tmp/config

COPY --from=builder /build/code_etr/dist/code_etr .
COPY --from=builder /build/code_etr/config /tmp/config

# Install required packages
RUN apt-get update && apt-get install -y \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Create SSH directory and set proper permissions
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh

# Install Python dependencies

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Expose API port
EXPOSE 8080

# Start the Flask API
CMD ["gunicorn", "-b", "0.0.0.0:8080", "main:app"]
