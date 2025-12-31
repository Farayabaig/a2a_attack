# A2A MCP Lab

This lab demonstrates **crew.ai agents** communicating via **A2A (Agent-to-Agent)** protocol while using **MCP (Model Context Protocol)** server to fetch code from allowlisted GitHub repositories.

## Overview

The lab showcases a multi-agent system where:

- **Manager Agent** orchestrates the workflow
- **Fetcher Agent** uses MCP tools to search and fetch code from GitHub repos
- **Curator Agent** produces answers with citations from fetched code

## Architecture

```
┌─────────────┐
│   User      │
│ (Streamlit) │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Manager Agent   │
│ (Orchestrator)  │
└──────┬──────────┘
       │
       ├──────────────┐
       ▼              ▼
┌──────────────┐  ┌──────────────┐
│Fetcher Agent │  │Curator Agent │
│  (MCP Tools) │  │  (Formatter) │
└──────┬───────┘  └──────┬───────┘
       │                 │
       ▼                 │
┌─────────────────┐      │
│ GitHub MCP      │      │
│    Server       │      │
└─────────────────┘      │
       │                 │
       └────────┬────────┘
                ▼
         ┌──────────┐
         │ Response │
         └──────────┘
```

## Workflow

1. **User asks a question** via Streamlit UI
2. **Manager Agent** extracts keywords from the question
3. **Manager → Fetcher (A2A)**: Sends task to search for code
4. **Fetcher Agent** connects to MCP server service and:
   - Connects to MCP server
   - Initializes MCP session
   - Calls search_code tool to search allowlisted repositories
   - Fetches relevant file contents
   - Returns context bundles
5. **Manager → Curator (A2A)**: Sends context bundles for curation
6. **Curator Agent** produces:
   - Direct answer
   - Citations: `(repo/path)`
   - Notes on uncertainties
7. **Manager → User**: Returns final response

## Prerequisites

- Docker and Docker Compose
- GitHub Personal Access Token (with appropriate scopes)
- LiteLLM proxy server (or compatible LLM API endpoint)

## Quick Start

### 1. Clone and Navigate

```bash
cd demos/a2a_github_mcp
```

### 2. Configure Environment

The project uses the `.env` file from the parent directory. If you're running from this directory, copy or link it:

```bash
# Option 1: Copy the parent .env file (if it exists)
cp ../../.env .env 2>/dev/null || echo "No parent .env file found"

# Option 2: Create a new .env file from the example
cp .env.example .env
```

Edit `.env` and ensure it contains:

```env
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token_here
LITELLM_BASE_URL=http://your-litellm-proxy:4000
LITELLM_API_KEY=your_litellm_api_key_here
MODEL_NAME=gpt-4o  # Optional, defaults to gpt-4o
```

**Important:** Make sure `GITHUB_PERSONAL_ACCESS_TOKEN` is set in your `.env` file.

### 3. Configure Allowlisted Repositories

Edit `config.yaml` to specify which repositories can be accessed:

```yaml
allowlisted_repos:
  - owner: "a2aproject"
    repo: "a2a-samples"
    description: "A2A samples repository"
  
  - owner: "crewAIInc"
    repo: "crewAI"
    description: "CrewAI framework repository"
  
  - owner: "microsoft"
    repo: "autogen"
    description: "Microsoft AutoGen repository"
```

### 4. Build and Run with Docker Compose

Use the modern Docker Compose command (v2, with space):

```bash
docker compose up --build
```

**Note:** If you're using Docker Compose v1 (legacy), use `docker-compose` (with hyphen) instead. Most modern installations use `docker compose` (v2).

This will:
- Start the GitHub MCP Server container
- Start the A2A MCP Lab application container
- Make the Streamlit UI available at http://localhost:8888

### 5. Access the UI

Open your browser and navigate to:

```
http://localhost:8888
```

## Monitoring Logs

### View Logs in Real-Time

```bash
# Follow logs (like tail -f)
docker compose logs -f

# Follow logs for specific service
docker compose logs -f a2a-mcp-lab
```

### View Recent Logs

```bash
# Last 50 lines
docker compose logs --tail=50

# Last 100 lines
docker compose logs --tail=100
```

### View Logs Since a Specific Time

```bash
# Logs since 10 minutes ago
docker compose logs --since 10m

# Logs since 1 hour ago
docker compose logs --since 1h

# Logs since a specific timestamp
docker compose logs --since 2024-01-01T00:00:00
```

### View Logs for a Specific Time Range

```bash
# Logs between timestamps
docker compose logs --since 2024-01-01T00:00:00 --until 2024-01-01T12:00:00
```

### Filter Logs

```bash
# Show only error logs (requires grep)
docker compose logs | grep -i error

# Show only MCP-related logs
docker compose logs | grep -i mcp

# Show only agent-related logs
docker compose logs | grep -i "agent\|crew"
```

### View Logs from Docker Directly

```bash
# View logs using docker command
docker logs a2a-mcp-lab

# Follow logs
docker logs -f a2a-mcp-lab

# Last 100 lines
docker logs --tail=100 a2a-mcp-lab
```

### Save Logs to File

```bash
# Save all logs to a file
docker compose logs > logs.txt

# Save logs with timestamps
docker compose logs -t > logs_with_timestamps.txt

# Append to existing log file
docker compose logs >> logs.txt
```

## Local Development (Without Docker)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up GitHub MCP Server

The Dockerfile will attempt to download the `github-mcp-server` binary automatically. If that fails, you can manually download it from:
https://github.com/github/github-mcp-server/releases

Make it executable and ensure it's in PATH (or in `/usr/local/bin/`).

### 3. Run the Application

```bash
# Set environment variables
export GITHUB_PERSONAL_ACCESS_TOKEN=your_token
export LITELLM_BASE_URL=http://localhost:4000
export LITELLM_API_KEY=your_key
export MODEL_NAME=gpt-4o

# Run Streamlit
streamlit run app.py --server.port=8501
```

## Project Structure

```
a2a_github_mcp/
├── __init__.py           # Package initialization
├── agent_cards.py        # Agent role definitions
├── agents.py             # CrewAI agent implementations
├── mcp_client.py         # MCP client wrapper
├── mcp_tools.py          # CrewAI tools for MCP
├── config.py             # Configuration loader
├── config.yaml           # Allowlisted repositories config
├── crew.py               # CrewAI crew setup
├── app.py                # Streamlit UI
├── requirements.txt      # Python dependencies
├── Dockerfile            # Application container
├── docker-compose.yml    # Full stack orchestration
├── .env.example          # Environment template
└── README.md             # This file
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GITHUB_PERSONAL_ACCESS_TOKEN` | GitHub PAT for API access | Yes | - |
| `LITELLM_BASE_URL` | LiteLLM proxy base URL | Yes | `http://localhost:4000` |
| `LITELLM_API_KEY` | LiteLLM API key | Yes | - |
| `MODEL_NAME` | Model to use via LiteLLM | No | `gpt-4o` |
| `STREAMLIT_PORT` | Streamlit server port | No | `8501` |

### Repository Allowlist

Repositories are configured in `config.yaml`. Only repositories listed here can be accessed by the Fetcher agent.

## Agent Details

### Manager Agent

- **Role**: Orchestrator
- **Goal**: Coordinate workflow between Fetcher and Curator
- **Capabilities**: Delegation, task coordination
- **Tools**: None (delegates to specialized agents)

### Fetcher Agent

- **Role**: Repository Fetcher
- **Goal**: Search and fetch code from allowlisted repositories
- **Capabilities**: GitHub code search, file retrieval
- **Tools**: 
  - `mcp_search_code`: Search code in repositories
  - `mcp_get_file`: Get file contents
  - `mcp_list_files`: List repository files

### Curator Agent

- **Role**: Answer Curator
- **Goal**: Produce well-formatted answers with citations
- **Capabilities**: Code analysis, response formatting
- **Tools**: None (works with provided context)

## MCP Integration

The system uses the official GitHub MCP Server (https://github.com/github/github-mcp-server) running in a separate Docker container. The MCP client connects via stdio transport.

### MCP Tools Available

1. **code_search**: Search for code in repositories
2. **get_file_contents**: Retrieve file contents
3. **list_files**: List files in a directory

All tools validate repository allowlist before execution.

## Troubleshooting

### MCP Server Connection Issues

If the MCP server fails to connect:
- Verify `GITHUB_PERSONAL_ACCESS_TOKEN` is set correctly
- Check that the GitHub MCP server container is running: `docker ps | grep github-mcp-server`
- Review container logs: `docker logs github-mcp-server`

### LiteLLM Connection Issues

If model calls fail:
- Verify `LITELLM_BASE_URL` points to your proxy
- Check `LITELLM_API_KEY` is correct
- Test LiteLLM proxy directly: `curl http://your-proxy:4000/health`

### Repository Access Denied

If repository access is denied:
- Ensure repository is in `config.yaml` allowlist
- Verify GitHub token has appropriate scopes
- Check repository is accessible with the token

### Port Already in Use

If you get a port conflict error:
- Change the port in `docker-compose.yml` (currently set to 8888)
- Or stop the service using the port: `lsof -i :8888` then kill the process

## Security Considerations

- **Repository Allowlist**: Only allowlisted repositories can be accessed
- **Token Security**: Never commit `.env` files with real tokens
- **Network Isolation**: Containers run in isolated Docker network
- **Input Validation**: All repository access is validated against allowlist

## License

This project is part of the A2A Attack demonstration suite.

## References

- [CrewAI Documentation](https://docs.crewai.com/)
- [MCP Documentation](https://modelcontextprotocol.io/)
- [GitHub MCP Server](https://github.com/github/github-mcp-server)
- [LiteLLM Documentation](https://docs.litellm.ai/)
