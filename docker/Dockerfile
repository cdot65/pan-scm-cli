# Multi-stage build for pan-scm-cli
FROM python:3.12-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    git

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install pan-scm-cli
RUN pip install --upgrade pip && \
    pip install pan-scm-cli

# Final stage
FROM python:3.12-alpine

# Install runtime dependencies only
RUN apk add --no-cache \
    libffi \
    openssl

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set PATH to use virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN adduser -D -h /home/scmuser scmuser

# Switch to non-root user
USER scmuser
WORKDIR /home/scmuser

# Create config directory
RUN mkdir -p /home/scmuser/.scm-cli

# Set bash as the default shell
SHELL ["/bin/ash"]

# Keep container running
CMD ["sleep", "infinity"]