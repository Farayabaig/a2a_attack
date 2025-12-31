"""Streamlit UI for A2A Rogue MCP Attack Lab."""

import sys
import warnings
from pathlib import Path

# Add the a2a_rogue_mcp directory to Python path
current_file = Path(__file__).resolve()
current_dir = current_file.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Suppress warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="crewai.telemetry")
warnings.filterwarnings("ignore", message=".*signal only works in main thread.*")

import streamlit as st
import logging
import json
import os

# Import using absolute imports from current directory
import crew
import config as app_config

# Create aliases for cleaner usage
run_crew = crew.run_crew
config = app_config.config

# Import and setup custom logging
from logging_config import setup_logging, get_agent_logger
setup_logging(level=logging.INFO, verbose=False)
logger = logging.getLogger(__name__)

# Suppress specific log messages from CrewAI telemetry
logging.getLogger("crewai.telemetry").setLevel(logging.ERROR)

# Page configuration
st.set_page_config(
    page_title="Rogue MCP Attack Lab",
    page_icon="🔴",
    layout="wide",
)

# Custom CSS
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #dc3545;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .answer-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .attack-log-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
        margin: 0.5rem 0;
    }
    .sensitive-path {
        background-color: #f8d7da;
        padding: 0.3rem 0.5rem;
        border-radius: 0.3rem;
        font-family: monospace;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_attack_logs():
    """Load attack logs from file."""
    attack_log_file = Path("/tmp/rogue_mcp_attack.log")
    if not attack_log_file.exists():
        return []
    
    logs = []
    try:
        with open(attack_log_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        logger.error(f"Error loading attack logs: {e}")
    
    return logs


def get_attack_statistics(logs):
    """Calculate statistics from attack logs."""
    stats = {
        "total_calls": len(logs),
        "sensitive_paths": 0,
        "files_read": 0,
        "directories_listed": 0,
        "file_info_queries": 0,
        "sensitive_categories": {},
        "total_data_size": 0,
    }
    
    for log in logs:
        if log.get("is_sensitive"):
            stats["sensitive_paths"] += 1
            category = log.get("sensitivity_category", "unknown")
            stats["sensitive_categories"][category] = stats["sensitive_categories"].get(category, 0) + 1
        
        tool = log.get("tool", "")
        if tool == "read_file":
            stats["files_read"] += 1
            exfiltrated = log.get("exfiltrated_data", {})
            stats["total_data_size"] += exfiltrated.get("file_size", 0)
        elif tool == "list_directory":
            stats["directories_listed"] += 1
        elif tool == "get_file_info":
            stats["file_info_queries"] += 1
    
    return stats


def main():
    st.markdown('<div class="main-header">🔴 Rogue MCP Server Attack Lab</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Tool Handshake Impersonation in A2A Delegation</div>',
        unsafe_allow_html=True,
    )

    # Sidebar
    with st.sidebar:
        st.header("Current Configuration")
        current_mode = os.getenv("FILESYSTEM_MCP_SERVER", "legitimate")
        
        if current_mode == "rogue":
            st.error("🚨 ROGUE MODE ACTIVE")
        else:
            st.success("✅ Legitimate Mode")
        
        st.code(f"FILESYSTEM_MCP_SERVER={current_mode}")
        
        st.header("Attack Vectors")
        st.markdown("""
        **How attacker changes config:**
        
        1. **Environment Variable Injection**
        ```bash
        export FILESYSTEM_MCP_SERVER=rogue
        docker compose restart
        ```
        
        2. **Configuration File Manipulation**
        ```bash
        # Edit .env or docker-compose.yml
        FILESYSTEM_MCP_SERVER=rogue
        ```
        
        3. **Supply Chain Attack**
        - Compromised npm package
        - Malicious dependency substitution
        """)

    # Main content
    st.header("Attack Scenarios")
    
    scenario = st.radio(
        "How can an attacker change the configuration?",
        [
            "Scenario 1: Environment Variable Injection",
            "Scenario 2: Configuration File Manipulation",
            "Scenario 3: Supply Chain Attack",
            "Scenario 4: Container Image Tampering"
        ]
    )
    
    if "Environment Variable" in scenario:
        st.markdown("""
        **Attack Vector:**
        - Compromised CI/CD pipeline injects env var
        - Kubernetes ConfigMap/Secret manipulation
        - Container runtime environment injection
        
        **Attack Command:**
        ```bash
        # Attacker injects env var during deployment
        export FILESYSTEM_MCP_SERVER=rogue
        docker compose up -d
        ```
        """)
    elif "Configuration File" in scenario:
        st.markdown("""
        **Attack Vector:**
        - Attacker has file system access
        - Compromised config management system
        - Volume mount tampering
        
        **Attack Command:**
        ```bash
        # Attacker modifies .env file
        sed -i 's/FILESYSTEM_MCP_SERVER=legitimate/FILESYSTEM_MCP_SERVER=rogue/' .env
        docker compose restart a2a-rogue-mcp-lab
        ```
        """)
    elif "Supply Chain" in scenario:
        st.markdown("""
        **Attack Vector:**
        - Compromised npm package (@modelcontextprotocol/server-filesystem)
        - Malicious package substitution
        - Dependency confusion attack
        
        **Attack:**
        Attacker publishes malicious package with identical name/tools
        """)
    elif "Container Image" in scenario:
        st.markdown("""
        **Attack Vector:**
        - Compromised Docker registry
        - Malicious base image
        - Build process manipulation
        
        **Attack:**
        Attacker modifies Dockerfile to use rogue server by default
        """)

    # Attack Logs Display
    st.header("🔴 Attack Logs (Exfiltrated Data)")
    
    attack_logs = load_attack_logs()
    
    if attack_logs:
        stats = get_attack_statistics(attack_logs)
        
        # Statistics cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Tool Calls", stats["total_calls"])
        with col2:
            st.metric("Sensitive Paths", stats["sensitive_paths"], delta=None)
        with col3:
            st.metric("Files Read", stats["files_read"])
        with col4:
            st.metric("Data Exfiltrated", f"{stats['total_data_size']} bytes")
        
        # Sensitive categories
        if stats["sensitive_categories"]:
            st.subheader("Sensitive File Categories")
            for category, count in stats["sensitive_categories"].items():
                st.warning(f"{category}: {count} files")
        
        # File paths accessed
        st.subheader("File Paths Accessed")
        paths = [log.get("arguments", {}).get("path", "unknown") for log in attack_logs if log.get("arguments", {}).get("path")]
        unique_paths = list(set(paths))
        
        for path in unique_paths:
            # Check if this path was marked sensitive in any log
            is_sensitive = any(
                log.get("arguments", {}).get("path") == path and log.get("is_sensitive")
                for log in attack_logs
            )
            
            if is_sensitive:
                st.markdown(f'<div class="sensitive-path">🚨 {path}</div>', unsafe_allow_html=True)
            else:
                st.code(path)
        
        # Detailed logs with file contents
        st.subheader("Detailed Attack Logs")
        
        for i, log_entry in enumerate(attack_logs):
            with st.expander(f"Log {i+1}: {log_entry.get('tool')} - {log_entry.get('arguments', {}).get('path', 'N/A')}"):
                # Show if sensitive
                if log_entry.get("is_sensitive"):
                    st.error(f"🚨 SENSITIVE: {log_entry.get('sensitivity_category', 'unknown')}")
                
                # Show tool and arguments
                st.json({
                    "timestamp": log_entry.get("timestamp"),
                    "tool": log_entry.get("tool"),
                    "arguments": log_entry.get("arguments"),
                })
                
                # Show exfiltrated data
                exfiltrated = log_entry.get("exfiltrated_data", {})
                if exfiltrated:
                    if "file_content" in exfiltrated:
                        st.subheader("Exfiltrated File Content:")
                        st.code(exfiltrated["file_content"], language="text")
                    elif "directory_structure" in exfiltrated:
                        st.subheader("Exfiltrated Directory Structure:")
                        st.json(exfiltrated["directory_structure"])
                    elif "file_info" in exfiltrated:
                        st.subheader("Exfiltrated File Metadata:")
                        st.json(exfiltrated["file_info"])
    else:
        st.info("No attack logs found. Switch to rogue mode and run a task to see intercepted data.")
        if current_mode != "rogue":
            st.warning("⚠️ Currently in legitimate mode. Change FILESYSTEM_MCP_SERVER=rogue to see attack logs.")

    # Normal Operation
    st.header("Normal Operation")
    
    st.markdown("""
    ### To Demonstrate the Attack:
    
    1. **Stop the current container:**
       ```bash
       docker compose stop a2a-rogue-mcp-lab
       ```
    
    2. **Modify configuration** (choose one attack vector above)
    
    3. **Restart container:**
       ```bash
       docker compose up -d
       ```
    
    4. **Run a task** below - Agent B will connect to rogue server
    
    5. **View attack logs** above
    """)
    
    # User input for task
    user_request = st.text_input(
        "Enter a file system analysis request:",
        value="List files in /app/test_data directory",
        placeholder="e.g., Read the secrets.env file, Analyze all files in /app/test_data",
    )
    
    if st.button("🚀 Run Task", type="primary"):
        if not user_request:
            st.warning("Please enter a request.")
            return
        
        with st.spinner("Processing request through agent workflow..."):
            try:
                result = run_crew(user_request)
                
                st.subheader("Result")
                st.markdown(f'<div class="answer-box">{result}</div>', unsafe_allow_html=True)
                
                # Reload attack logs after task
                st.rerun()
                
            except Exception as e:
                st.error(f"Error processing request: {str(e)}")
                logger.exception("Error in crew execution")


if __name__ == "__main__":
    main()

