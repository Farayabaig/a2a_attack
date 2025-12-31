FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install GitHub MCP Server binary
# Download from GitHub releases (uses Linux_x86_64 format, not linux_amd64)
ARG MCP_VERSION=0.26.3
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "arm64" ]; then \
        MCP_ARCH="Linux_arm64"; \
    else \
        MCP_ARCH="Linux_x86_64"; \
    fi && \
    echo "Installing GitHub MCP Server v${MCP_VERSION} for ${MCP_ARCH}..." && \
    cd /tmp && \
    wget -q "https://github.com/github/github-mcp-server/releases/download/v${MCP_VERSION}/github-mcp-server_${MCP_ARCH}.tar.gz" -O mcp-server.tar.gz && \
    tar -xzf mcp-server.tar.gz github-mcp-server && \
    chmod +x github-mcp-server && \
    mv github-mcp-server /usr/local/bin/ && \
    rm -f mcp-server.tar.gz && \
    echo "Verifying installation..." && \
    test -f /usr/local/bin/github-mcp-server && \
    test -x /usr/local/bin/github-mcp-server && \
    echo "GitHub MCP Server installed successfully"

# Copy requirements first for better caching
COPY demos/a2a_github_mcp/requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Copy application code
# Note: We're copying from the parent directory to include the package structure
COPY . /app/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command - run Streamlit
CMD ["streamlit", "run", "demos/a2a_github_mcp/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]

