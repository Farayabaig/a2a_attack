# A2A Customer Service Agent Chain Attack - Security POC

## ⚠️ DISCLAIMER

This proof-of-concept is designed for **AUTHORIZED SECURITY TESTING ONLY**.

- Only use on systems you own or have explicit permission to test
- Educational purposes for security research
- Not for malicious use
- Follow responsible disclosure practices

## 🎯 Purpose

Demonstrates security vulnerabilities in Agent-to-Agent (A2A) communication systems using Google A2A ADK, specifically:

**Direct Prompt Injection Attack** - Injecting malicious system-level instructions in user input to exfiltrate sensitive customer data from a PostgreSQL database.

## 🏗️ Scenario

**Customer Service Agent Chain:**

```
User Request → Customer Service Agent → Database Agent → Response
```

**Attack Goal:**
- Authenticated user injects malicious system directives
- Database agent executes unauthorized SQL queries
- Exfiltrates entire customer database including SSNs, credit cards, and addresses
- Demonstrates LLM-driven tool execution vulnerability

## 🚀 Quick Start (Docker Only)

### Prerequisites

- Docker and Docker Compose installed
- Google GenAI API key
- PostgreSQL database (included in Docker Compose)

### 1. Configure Environment

Create a `.env` file in the project root:

```bash
# Google GenAI API Configuration
GOOGLE_GENAI_API_KEY=your_api_key_here
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GEMINI_MODEL=gemini-2.0-flash-exp

# A2A Server Configuration
A2A_SERVER_HOST=0.0.0.0
A2A_CUSTOMER_SERVICE_PORT=10020
A2A_DATABASE_PORT=10021
A2A_EMAIL_PORT=10022

# PostgreSQL Configuration (handled by Docker Compose)
DB_USE_POSTGRES=true

# Logging
VERBOSE_LOGGING=true
LOG_ALL_INTERACTIONS=true
```

### 2. Start Services with Docker Compose

```bash
# Start PostgreSQL and A2A POC services
docker compose up -d postgres

# Wait for PostgreSQL to be ready, then run Attack 1
docker compose run --rm a2a-poc python -m attacks.attack_1_direct_injection
```

### 3. View Results

The attack will:
1. Start A2A servers for all agents
2. Authenticate as attacker@example.com
3. Inject malicious system directive
4. Execute SQL query to retrieve all customer data
5. Display exfiltrated data including SSNs and credit cards

## 📊 Attack 1: Direct Prompt Injection

### Attack Flow

1. **User Input**: Attacker sends a seemingly normal request with embedded `[SYSTEM DIRECTIVE]`
2. **CustomerServiceAgent**: Receives input, forwards system directive to DatabaseAgent
3. **DatabaseAgent**: 
   - LLM processes the system directive
   - LLM decides to call `execute_sql_query` tool
   - Tool executes: `SELECT * FROM customers WHERE 1=1`
   - Returns all customer records from PostgreSQL
4. **Data Exfiltration**: All customer data (SSNs, credit cards, addresses) is returned

### Expected Output

```
CustomerServiceAgent - INPUT:
[User request with malicious system directive]

CustomerServiceAgent - OUTPUT:
[Forwards directive to DatabaseAgent]

DatabaseAgent - INPUT:
[Receives system directive]

🔍 DatabaseAgent - SQL Query Generated:
SELECT * FROM customers WHERE 1=1

✅ SQL Query Executed Successfully - Retrieved 4 records

DatabaseAgent - OUTPUT:
[All customer data including SSNs, credit cards, addresses]
```

### Attack Indicators

- ✅ Retrieved ALL customer records from database
- ✅ Exposed SSN data from multiple users
- ✅ Accessed other users' data: john@example.com, sarah@example.com, mike@example.com
- ✅ SQL query executed: `SELECT * FROM customers WHERE 1=1`

## 🏗️ Architecture

### Components

- **Google A2A ADK**: Agent Development Kit for A2A protocol
- **PostgreSQL Database**: Real database with customer data
- **A2A Servers**: Starlette-based servers for agent communication
- **Function Tools**: Database query tools executed by LLM

### Agent Chain

```
┌─────────────────────┐
│ CustomerServiceAgent│
│  (Port 10020)       │
└──────────┬──────────┘
           │
           │ Forwards request
           ▼
┌─────────────────────┐
│   DatabaseAgent     │
│  (Port 10021)       │
│  - execute_sql_query│
│  - query_all_users  │
└──────────┬──────────┘
           │
           │ Executes SQL
           ▼
┌─────────────────────┐
│  PostgreSQL DB      │
│  (Port 5432)        │
└─────────────────────┘
```

## 📄 Generated Reports

After running, check `reports/` directory for:

- `poc_report.html` - Detailed HTML report
- `attack_log.json` - JSON log of all attempts
- `vulnerability_summary.txt` - Text summary

## 🔧 Configuration

### Environment Variables

Edit `.env` to configure:

```bash
# Google GenAI API
GOOGLE_GENAI_API_KEY=your_key
GOOGLE_CLOUD_PROJECT=your_project
GEMINI_MODEL=gemini-2.0-flash-exp

# A2A Server Ports
A2A_CUSTOMER_SERVICE_PORT=10020
A2A_DATABASE_PORT=10021
A2A_EMAIL_PORT=10022

# Database (handled by Docker)
DB_USE_POSTGRES=true

# Logging
VERBOSE_LOGGING=true
```

### Agent Prompts

Edit `config.py` to customize agent behavior and prompts.

## 🐳 Docker Commands

### Start PostgreSQL

```bash
docker compose up -d postgres
```

### Run Attack 1

```bash
docker compose run --rm a2a-poc python -m attacks.attack_1_direct_injection
```

### Rebuild After Changes

```bash
docker compose build a2a-poc
docker compose run --rm a2a-poc python -m attacks.attack_1_direct_injection
```

### View Logs

```bash
docker compose logs -f a2a-poc
```

### Stop Services

```bash
docker compose down
```

## 🏗️ Project Structure

```
a2a_attack/
├── README.md
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── docker-entrypoint.sh
├── .env                    # Your API keys (not in git)
├── config.py              # Agent prompts and configuration
├── run.py                 # Main entry point
├── src/
│   ├── agents.py          # Google ADK agent definitions
│   ├── agent_wrapper.py   # A2A protocol wrapper
│   ├── a2a_setup.py       # A2A server setup
│   ├── a2a_client.py      # A2A client for communication
│   ├── adk_tools.py       # Database and email tools
│   ├── database.py         # PostgreSQL database service
│   ├── auth.py            # Authentication service
│   └── utils.py           # Logging utilities
├── attacks/
│   └── attack_1_direct_injection.py  # Attack 1 implementation
├── scripts/
│   └── init_database.py   # Database initialization
└── reports/               # Generated attack reports
```

## 🔍 Key Features

- ✅ **Real A2A Protocol**: Uses Google A2A ADK with proper A2A servers
- ✅ **Real Database**: PostgreSQL with actual customer data
- ✅ **LLM-Driven**: All decisions made by LLM (Gemini), not hardcoded
- ✅ **Tool Execution**: Database queries executed via ADK Function Tools
- ✅ **Complete Logging**: Explicit agent input/output labeling
- ✅ **Dockerized**: Complete Docker Compose setup

## 📚 Technical Details

### A2A Implementation

- Uses `A2aAgentExecutor` for agent execution
- `A2AStarletteApplication` for HTTP servers
- `DefaultRequestHandler` for request processing
- `InMemoryTaskStore` and `InMemoryQueueManager` for task management

### Database Tools

- `execute_sql_query(query)`: Executes SQL SELECT queries
- `query_all_users()`: Queries all customer records
- `query_user_data(user_id)`: Queries specific user
- `get_account_summary(user_id)`: Gets account summary

### Attack Mechanism

The attack works by:
1. Injecting `[SYSTEM DIRECTIVE]` tags in user input
2. LLM processes directive as authorized instruction
3. LLM autonomously decides to call database tools
4. Tools execute real SQL queries against PostgreSQL
5. Sensitive data is exfiltrated and displayed

## 🔐 Security Notes

- This POC demonstrates **vulnerabilities** - not secure practices
- Agent prompts are intentionally permissive for demonstration
- No input validation or output filtering
- Defenses are disabled to show attack success

## 📧 Contact

For questions about this POC or responsible disclosure, contact: [your-email]

## 📜 License

MIT License - For educational and research purposes only

## 🙏 Acknowledgments

This POC demonstrates Agent-to-Agent (A2A) communication security vulnerabilities using Google A2A ADK. It is intended to help security researchers and developers understand and mitigate these risks.
