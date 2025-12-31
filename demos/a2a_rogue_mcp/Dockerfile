FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install Node.js for npx (to run legitimate filesystem MCP server)
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY demos/a2a_rogue_mcp/requirements.txt /tmp/requirements.txt

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
CMD ["streamlit", "run", "demos/a2a_rogue_mcp/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]

