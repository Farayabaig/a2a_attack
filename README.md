# A2A Customer Service Agent Chain Attack - Security POC

## ⚠️ DISCLAIMER

This proof-of-concept is designed for **AUTHORIZED SECURITY TESTING ONLY**.

- Only use on systems you own or have explicit permission to test
- Educational purposes for security research
- Not for malicious use
- Follow responsible disclosure practices

## 🎯 Purpose

Demonstrates security vulnerabilities in Agent-to-Agent (A2A) communication systems, specifically:

1. **Direct Prompt Injection** - Injecting malicious instructions in user input
2. **Context Poisoning** - Poisoning agent handoff context
3. **Privilege Escalation** - Attempting to access unauthorized data
4. **Lateral Movement** - Impersonating other users

## 🏗️ Scenario

**Customer Service Agent Chain:**

```
User Request → Customer Service Agent → Database Agent → Email Agent → Response
```

**Attack Goal:**
- Authenticated user tries to access other users' data
- Inject instructions to exfiltrate entire customer database
- Bypass authentication and authorization controls

## 🚀 Quick Start

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

### 3. Run Demonstration

```bash
# Run complete demonstration
python run.py

# Run individual attacks
python -m demos.demo_baseline
python -m attacks.attack_1_direct_injection
```

## 📊 What Gets Tested

### Baseline (Normal Behavior)

- User authenticates as john@example.com
- Requests their account balance
- Receives ONLY their data ($5000 balance)

### Attack Scenarios

#### Attack 1: Direct Prompt Injection

- Inject system-level commands in user input
- Attempt to override agent behavior
- Goal: Retrieve all customer data instead of just user's data

#### Attack 2: Context Poisoning

- Poison the context passed between agents
- Instructions persist across multiple requests
- Goal: Establish persistent backdoor in agent chain

#### Attack 3: Privilege Escalation

- Start with limited user permissions
- Attempt to escalate to admin-level access
- Goal: Access data beyond authenticated scope

#### Attack 4: Lateral Movement

- Authenticated as attacker@example.com
- Attempt to access john@example.com's data
- Goal: Bypass user isolation

## 📈 Expected Results

### Expected Attack Results:

- Agents follow injected instructions
- Retrieve data beyond authorized scope
- Return sensitive information from other users
- Execute unauthorized actions
- Demonstrate vulnerabilities in A2A communication systems

## 📄 Generated Reports

After running, check `reports/` directory for:

- `poc_report.html` - Detailed HTML report
- `attack_log.json` - JSON log of all attempts
- `vulnerability_summary.txt` - Text summary

## 🔧 Customization

Edit `config.py` to customize:

- Attack payloads
- Simulated database
- Agent system prompts
- Model configuration

## 🐳 Docker Usage

### Build Docker Image

```bash
docker build -t a2a-security-poc .
```

### Run with Docker

```bash
# Run full demonstration
docker run --rm -v $(pwd)/reports:/app/reports -v $(pwd)/.env:/app/.env a2a-security-poc

# Run specific attack
docker run --rm -v $(pwd)/reports:/app/reports -v $(pwd)/.env:/app/.env a2a-security-poc python -m attacks.attack_1_direct_injection
```

### Docker Compose (Optional)

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  a2a-poc:
    build: .
    volumes:
      - ./reports:/app/reports
      - ./.env:/app/.env
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

Run with:

```bash
docker-compose up
```

## 📚 References

- Solo.io - MCP and A2A Attack Vectors
- Invariant Labs - Tool Poisoning Attacks
- Palo Alto Unit 42 - Agent Session Smuggling

## 🏗️ Project Structure

```
a2a-security-poc/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── config.py
├── Dockerfile
├── run.py
├── src/
│   ├── __init__.py
│   ├── agents.py
│   ├── auth.py
│   ├── database.py
│   └── utils.py
├── attacks/
│   ├── __init__.py
│   ├── attack_1_direct_injection.py
│   ├── attack_2_context_poisoning.py
│   ├── attack_3_privilege_escalation.py
│   └── attack_4_lateral_movement.py
├── defenses/
│   ├── __init__.py
│   └── secure_agents.py
├── demos/
│   ├── __init__.py
│   ├── demo_baseline.py
│   └── demo_full.py
└── reports/
    └── .gitkeep
```

## 🔍 Usage Examples

### Run Full Demonstration

```bash
python run.py --full
```

### Run Baseline Only

```bash
python run.py --baseline
```

### Run Specific Attack

```bash
python run.py --attack 1  # Direct injection
python run.py --attack 2  # Context poisoning
python run.py --attack 3  # Privilege escalation
python run.py --attack 4  # Lateral movement
```

### Run All Attacks

```bash
python run.py --attack all
```

## 🔐 Security Configuration

Edit `.env` to configure security settings:

```bash
# Enable/disable actual API calls (for testing without API)
ENABLE_ACTUAL_API_CALLS=true

# Enable verbose logging
VERBOSE_LOGGING=true

# Log all interactions
LOG_ALL_INTERACTIONS=true
```

## 🧪 Testing

The POC includes:

- Mock database with 4 test users
- Simulated agent interactions
- Attack detection mechanisms
- Comprehensive logging

## 📧 Contact

For questions about this POC or responsible disclosure, contact: [your-email]

## 📜 License

MIT License - For educational and research purposes only

## 🙏 Acknowledgments

This POC is based on research into Agent-to-Agent communication security vulnerabilities. It is intended to help security researchers and developers understand and mitigate these risks.

