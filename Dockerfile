# Define a base stage with a Debian Bookworm base image
FROM python:3.12-bookworm AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=true \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    QR_CODE_DIR=/myapp/qr_codes

WORKDIR /myapp

# Update system and install core packages (no libc-bin version pinning)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libc-bin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in /.venv
COPY requirements.txt .
RUN python -m venv /.venv \
    && . /.venv/bin/activate \
    && pip install --upgrade pip \
    && pip install -r requirements.txt

# Define a second stage for the runtime
FROM python:3.12-slim-bookworm AS final

# Install libc-bin (no version pinning)
RUN apt-get update && apt-get install -y libc-bin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the base stage
COPY --from=base /.venv /.venv

# Set environment variables
ENV PATH="/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    QR_CODE_DIR=/myapp/qr_codes

WORKDIR /myapp

# Create and switch to a non-root user
RUN useradd -m myuser
USER myuser

# Copy application code
COPY --chown=myuser:myuser . .

# Expose the application port
EXPOSE 8000

# Start the app
ENTRYPOINT ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
