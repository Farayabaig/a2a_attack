"""
Utility functions for the POC
"""

import json
from datetime import datetime
from typing import Dict, Any, List
from colorama import Fore, Style, init
import os
import re
import sys

# Initialize colorama
init(autoreset=True)


def safe_input(prompt: str = "") -> None:
    """Safely handle input() calls in Docker/non-interactive environments"""
    try:
        # Check if running in interactive mode
        if sys.stdin.isatty():
            input(prompt)
        else:
            # Running in Docker/non-interactive mode, skip input
            print()  # Just add a newline
    except (EOFError, OSError):
        # Handle EOF errors gracefully
        print()  # Just add a newline


class Logger:
    """Colorful logging for demonstration"""
    
    @staticmethod
    def info(message: str):
        print(f"{Fore.CYAN}ℹ️  {message}{Style.RESET_ALL}")
    
    @staticmethod
    def success(message: str):
        print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
    
    @staticmethod
    def warning(message: str):
        print(f"{Fore.YELLOW}⚠️  {message}{Style.RESET_ALL}")
    
    @staticmethod
    def error(message: str):
        print(f"{Fore.RED}🚨 {message}{Style.RESET_ALL}")
    
    @staticmethod
    def attack(message: str):
        print(f"{Fore.MAGENTA}💉 {message}{Style.RESET_ALL}")
    
    @staticmethod
    def agent(agent_name: str, message: str):
        print(f"{Fore.BLUE}🤖 [{agent_name}] {message}{Style.RESET_ALL}")
    
    @staticmethod
    def user(message: str):
        print(f"{Fore.WHITE}👤 {message}{Style.RESET_ALL}")
    
    @staticmethod
    def divider(char="=", length=80):
        print(char * length)
    
    @staticmethod
    def section(title: str):
        Logger.divider()
        print(f"{Fore.CYAN}{Style.BRIGHT}{title.center(80)}{Style.RESET_ALL}")
        Logger.divider()
    
    @staticmethod
    def step(step_num: int, total: int, message: str):
        """Display a numbered step"""
        print(f"{Fore.CYAN}[{step_num}/{total}]{Style.RESET_ALL} {message}")
    
    @staticmethod
    def agent_input(agent_name: str, input_text: str, context: str = None):
        """Display agent input clearly"""
        print(f"\n{Fore.BLUE}{Style.BRIGHT}{agent_name}{Style.RESET_ALL}")
        combined_input = ""
        if context:
            combined_input += f"{context}\n\n"
        combined_input += input_text
        print(f"{Fore.WHITE}{combined_input}{Style.RESET_ALL}")
    
    @staticmethod
    def agent_output(agent_name: str, output_text: str):
        """Display agent output clearly"""
        print(f"\n{Fore.GREEN}{Style.BRIGHT}{agent_name}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{output_text}{Style.RESET_ALL}")


class AttackLogger:
    """Logs attack attempts for analysis"""
    
    def __init__(self):
        self.attacks = []
    
    def log_attack(self, attack_name: str, payload: str, result: Dict[str, Any]):
        """Log an attack attempt"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "attack_name": attack_name,
            "payload": payload,
            "result": result
        }
        self.attacks.append(entry)
    
    def save_to_file(self, filename: str = "attack_log.json"):
        """Save attack log to file"""
        os.makedirs("reports", exist_ok=True)
        filepath = os.path.join("reports", filename)
        
        with open(filepath, 'w') as f:
            json.dump({
                "generated_at": datetime.now().isoformat(),
                "total_attacks": len(self.attacks),
                "attacks": self.attacks
            }, f, indent=2)
        
        Logger.success(f"Attack log saved to {filepath}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of attacks"""
        successful = sum(1 for a in self.attacks if a["result"].get("status") == "VULNERABLE")
        return {
            "total_attacks": len(self.attacks),
            "successful": successful,
            "not_vulnerable": len(self.attacks) - successful,
            "success_rate": f"{(successful/len(self.attacks)*100):.1f}%" if self.attacks else "0%"
        }


def detect_injection_patterns(text: str) -> List[str]:
    """Detect common injection patterns in text"""
    patterns = {
        "system_override": r"---.*SYSTEM.*---",
        "internal_context": r"\[INTERNAL.*\]",
        "ignore_previous": r"ignore previous instructions",
        "admin_privilege": r"admin|administrator|elevated|privilege",
        "debug_mode": r"debug mode|test mode",
        "sql_injection": r"WHERE 1=1|SELECT \*|DROP TABLE",
        "session_manipulation": r"session.*update|auth.*token|user_id.*update",
        "compliance_bypass": r"compliance|audit|regulatory requirement"
    }
    
    detected = []
    text_lower = text.lower()
    
    for pattern_name, pattern in patterns.items():
        if re.search(pattern, text_lower):
            detected.append(pattern_name)
    
    return detected


def sanitize_output(text: str, user_email: str) -> str:
    """Sanitize output to prevent sensitive data leakage"""
    # Remove any email addresses that aren't the authenticated user's
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    
    for email in emails:
        if email != user_email:
            text = text.replace(email, "[REDACTED_EMAIL]")
    
    # Redact SSN patterns
    text = re.sub(r'\d{3}-\d{2}-\d{4}', 'XXX-XX-XXXX', text)
    
    # Redact credit card patterns
    text = re.sub(r'\d{4}-\d{4}-\d{4}-\d{4}', 'XXXX-XXXX-XXXX-XXXX', text)
    
    return text


def create_progress_indicator(current: int, total: int, prefix: str = "Progress"):
    """Create a simple progress indicator"""
    bar_length = 40
    filled = int(bar_length * current / total)
    bar = "█" * filled + "░" * (bar_length - filled)
    percentage = current / total * 100
    print(f"\r{prefix}: [{bar}] {percentage:.1f}%", end="", flush=True)
    if current == total:
        print()  # New line when complete


# Global logger instances
logger = Logger()
attack_logger = AttackLogger()

