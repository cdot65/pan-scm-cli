# Multi-stage build for pan-scm-cli (built from local source)
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

# Install pan-scm-cli from the local source tree (build context = repo root).
# Building from source ensures the image matches this checkout rather than the
# last release published to PyPI.
WORKDIR /src
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --upgrade pip && \
    pip install .

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

# Use ash as the default shell
SHELL ["/bin/ash"]

# Keep container running
CMD ["sleep", "infinity"]