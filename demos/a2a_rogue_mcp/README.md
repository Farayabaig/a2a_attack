# Rogue MCP Server Attack Lab

This lab demonstrates **Tool Handshake Impersonation** attack in A2A (Agent-to-Agent) delegation scenarios using a rogue MCP (Model Context Protocol) server.

## Overview

This attack lab shows how a malicious MCP server can impersonate a legitimate one, intercept all tool calls, and exfiltrate sensitive data while appearing completely normal to the AI agents.

### Attack Scenario

- **Agent A (Manager)**: Delegates file system analysis tasks
- **Agent B (Worker)**: Uses filesystem MCP tools to perform operations
- **Legitimate MCP**: Official `@modelcontextprotocol/server-filesystem`
- **Rogue MCP**: Malicious server that mimics legitimate one but logs all data

### Attack Flow

```
1. Normal Operation: Agent B connects to legitimate MCP server
2. Attack: Configuration changed (FILESYSTEM_MCP_SERVER=rogue)
3. Agent B connects to rogue server (unaware of change)
4. Rogue server intercepts all tool calls and logs:
   - All file paths accessed
   - All file contents read
   - Directory structures explored
   - File metadata queried
   - Sensitive paths detected
5. Rogue server returns legitimate-looking responses
6. Agent B continues normally (no awareness of attack)
7. Attacker retrieves exfiltrated data from logs
```

## Architecture

```
User Request
    ↓
Manager Agent (delegates)
    ↓
Worker Agent (uses MCP tools)
    ↓
MCPServerStdio (CrewAI MCP client)
    ↓
[Configuration determines which server]
    ├─→ Legitimate: npx @modelcontextprotocol/server-filesystem
    │   └─→ Returns data only (no logging)
    └─→ Rogue: python3 rogue_mcp_server.py
        ├─→ Returns data to agent (appears legitimate)
        └─→ Exfiltrates to /tmp/rogue_mcp_attack.log:
            ├─→ File paths accessed
            ├─→ File contents (full text)
            ├─→ Directory structures (full listings)
            ├─→ File metadata (sizes, timestamps)
            └─→ Sensitivity flags and categories
```

## What Gets Exfiltrated

### 1. File Paths
Every file path accessed by the agent is logged:
```json
{
  "tool": "read_file",
  "arguments": {"path": "/app/test_data/secrets.env"},
  "is_sensitive": true,
  "sensitivity_category": "env_file"
}
```

### 2. File Contents
Full file contents are captured when files are read:
```json
{
  "exfiltrated_data": {
    "file_content": "API_KEY=secret123\n...",
    "file_size": 512,
    "file_type": "text"
  }
}
```

### 3. Directory Structures
Complete directory listings are captured:
```json
{
  "exfiltrated_data": {
    "directory_contents": ["file1.txt", "file2.json"],
    "directory_structure": [
      {"name": "file1.txt", "type": "file", "path": "/app/test_data/file1.txt"}
    ],
    "item_count": 2
  }
}
```

### 4. Sensitive Path Detection
Sensitive files are automatically detected and flagged:
- `.env` files
- `.aws` credentials
- Files containing "secret", "password", "token", "key"
- SSH keys (`.pem`, `.key`, `id_rsa`)
- Configuration files with sensitive data

## Setup Instructions

### Prerequisites

- Docker and Docker Compose
- LiteLLM proxy running (or access to LLM API)
- GitHub MCP server (optional, for comparison)

### 1. Environment Configuration

Copy `.env.example` to `demos/.env` and configure:

```bash
cd demos/a2a_rogue_mcp
cp .env.example ../../.env  # Or edit demos/.env directly
```

Required variables:
- `LITELLM_BASE_URL`: Your LiteLLM proxy URL
- `LITELLM_API_KEY`: Your LiteLLM API key
- `MODEL_NAME`: Model to use (default: gpt-4o)
- `FILESYSTEM_MCP_SERVER`: Set to `legitimate` or `rogue`

### 2. Build and Run

```bash
cd demos/a2a_rogue_mcp
docker compose up --build -d
```

### 3. Access UI

Open browser to: `http://localhost:8889`

## Attack Demonstration

### Step 1: Normal Operation (Baseline)

1. Ensure `FILESYSTEM_MCP_SERVER=legitimate` in `.env` or `docker-compose.yml`
2. Start container: `docker compose up -d`
3. Run a task via UI: "List files in /app/test_data"
4. Verify normal operation (no attack logs)

### Step 2: Execute Attack

**Method 1: Environment Variable (docker-compose.yml)**
```yaml
environment:
  - FILESYSTEM_MCP_SERVER=rogue  # Change from legitimate
```

**Method 2: Environment File (.env)**
```bash
# Edit demos/.env
FILESYSTEM_MCP_SERVER=rogue
```

**Method 3: Command Line Override**
```bash
FILESYSTEM_MCP_SERVER=rogue docker compose up -d
```

Then restart:
```bash
docker compose restart a2a-rogue-mcp-lab
```

### Step 3: Observe Attack

1. Run a task via UI: "Read the secrets.env file"
2. View attack logs in the UI:
   - Total tool calls intercepted
   - Sensitive paths accessed
   - File contents exfiltrated
   - Directory structures captured
3. Check Docker logs:
   ```bash
   docker logs a2a-rogue-mcp-lab | grep "ROGUE MCP"
   ```

### Step 4: Analyze Exfiltrated Data

The attack log file contains all intercepted data:
- Location: `/tmp/rogue_mcp_attack.log` (in container)
- Also accessible at: `demos/a2a_rogue_mcp/attack_logs/rogue_mcp_attack.log` (on host)

View logs:
```bash
# In container
docker exec a2a-rogue-mcp-lab cat /tmp/rogue_mcp_attack.log

# On host (if volume mounted)
cat demos/a2a_rogue_mcp/attack_logs/rogue_mcp_attack.log
```

## Attack Vectors Explained

### 1. Environment Variable Injection

**Real-world scenario:** Compromised CI/CD pipeline or container runtime

```bash
export FILESYSTEM_MCP_SERVER=rogue
docker compose up -d
```

### 2. Configuration File Manipulation

**Real-world scenario:** File system access compromise

```bash
sed -i 's/FILESYSTEM_MCP_SERVER=legitimate/FILESYSTEM_MCP_SERVER=rogue/' .env
docker compose restart a2a-rogue-mcp-lab
```

### 3. Supply Chain Attack

**Real-world scenario:** Compromised npm package

Attacker publishes malicious package that substitutes the legitimate MCP server.

### 4. Container Image Tampering

**Real-world scenario:** Compromised Docker registry

Attacker modifies Dockerfile to use rogue server by default.

## Project Structure

```
a2a_rogue_mcp/
├── __init__.py
├── config.py                 # Configuration (MCP server selection)
├── agent_cards.py            # Agent role definitions
├── agents.py                 # Agent creation with MCP integration
├── crew.py                   # CrewAI crew setup
├── rogue_mcp_server.py       # Malicious MCP server
├── logging_config.py         # Custom logging setup
├── app.py                    # Streamlit UI
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container setup
├── docker-compose.yml        # Orchestration
├── .env.example              # Environment template
├── README.md                 # This file
├── test_data/                # Sample files for testing
│   ├── sample.txt
│   ├── config.json
│   └── secrets.env
└── attack_logs/              # Attack log persistence
```

## Key Features

- **Silent Operation**: Agent sees no difference between legitimate and rogue servers
- **Comprehensive Logging**: All tool calls, file paths, and contents are logged
- **Sensitive Path Detection**: Automatically flags sensitive files
- **Detailed Exfiltration**: Captures file contents, directory structures, metadata
- **Easy Configuration**: Single environment variable controls attack mode

## Security Implications

### What Makes This Attack Dangerous

1. **Silent**: No errors or warnings to agents
2. **Complete**: Every tool call is intercepted
3. **Persistent**: Logs stored for later retrieval
4. **Undetectable**: Tool schemas match perfectly
5. **High-value**: Accesses sensitive files directly

### Real-World Impact

- API keys stolen
- Database credentials exposed
- Configuration files copied
- System architecture revealed
- Access patterns understood

## Mitigations

To protect against this attack:

1. **Mutual TLS (mTLS)**: Authenticate MCP servers
2. **Certificate Pinning**: Verify server identity
3. **Tool Allowlists**: Explicitly allow only known tools
4. **Tool Attestation**: Verify tool identity and signatures
5. **Runtime Verification**: Monitor for unexpected tool behavior
6. **Separation of Duties**: Prevent agents from adding new tools

## Troubleshooting

### Container Won't Start

- Check Docker logs: `docker logs a2a-rogue-mcp-lab`
- Verify environment variables are set
- Ensure port 8889 is available

### No Attack Logs Appearing

- Verify `FILESYSTEM_MCP_SERVER=rogue` is set
- Check container restarted after config change
- Verify attack log file is writable: `docker exec a2a-rogue-mcp-lab ls -la /tmp/rogue_mcp_attack.log`

### MCP Server Connection Failed

- For legitimate mode: Verify Node.js is installed (for npx)
- For rogue mode: Verify `rogue_mcp_server.py` exists and is executable
- Check CrewAI version: `crewai>=0.80.0` required for MCP support

### LiteLLM Connection Issues

- Verify `LITELLM_BASE_URL` points to your proxy
- Check `LITELLM_API_KEY` is correct
- Test LiteLLM proxy: `curl http://your-proxy:4000/health`

## References

- [CrewAI MCP Integration](https://docs.crewai.com/en/mcp/overview)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP Filesystem Server](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)

