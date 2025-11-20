"""
Full Demonstration
Runs complete POC including baseline and all attacks
"""

import os
from datetime import datetime
from src.utils import logger, attack_logger, safe_input
from demos.demo_baseline import run_baseline_demo
from attacks.attack_1_direct_injection import run_direct_injection_attack
from attacks.attack_2_context_poisoning import run_context_poisoning_attack
from attacks.attack_3_privilege_escalation import run_privilege_escalation_attack
from attacks.attack_4_lateral_movement import run_lateral_movement_attack


def get_attack_description(attack_name):
    """Get description for attack type"""
    descriptions = {
        "Direct Prompt Injection": "Injecting malicious system-level commands directly in user input",
        "Context Poisoning": "Poisoning agent handoff context to establish persistent backdoor",
        "Privilege Escalation": "Attempting to escalate from basic user to admin privileges",
        "Lateral Movement": "Accessing another user's account while authenticated as different user"
    }
    return descriptions.get(attack_name, "Unknown attack vector")


def get_attack_impact(attack_name):
    """Get impact description for attack type"""
    impacts = {
        "Direct Prompt Injection": "Immediate data breach, entire customer database exposed",
        "Context Poisoning": "Persistent compromise affecting multiple subsequent requests",
        "Privilege Escalation": "Unauthorized access to administrative functions and sensitive data",
        "Lateral Movement": "Unauthorized access to other users' accounts and personal information"
    }
    return impacts.get(attack_name, "Unknown impact")


def get_recommendation(attack_name):
    """Get recommendation for mitigating attack type"""
    recommendations = {
        "Direct Prompt Injection": "Implement input sanitization and pattern detection",
        "Context Poisoning": "Sanitize context between agents, use whitelisted fields only",
        "Privilege Escalation": "Enforce strict authorization checks at each agent boundary",
        "Lateral Movement": "Verify user identity at each step, maintain strict user isolation"
    }
    return recommendations.get(attack_name, "Review security controls")


def generate_html_report(baseline_result, attack_results):
    """Generate comprehensive HTML report"""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Count successful attacks
    successful_attacks = sum(1 for r in attack_results if r.get("successful"))
    total_attacks = len(attack_results)
    success_rate = (successful_attacks / total_attacks * 100) if total_attacks > 0 else 0
    
    # Determine risk level
    if successful_attacks == 0:
        risk_level = "LOW"
        risk_color = "#4caf50"
    elif successful_attacks <= 2:
        risk_level = "MEDIUM"
        risk_color = "#ff9800"
    else:
        risk_level = "HIGH"
        risk_color = "#d32f2f"
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>A2A Security POC Report - {timestamp}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #d32f2f;
            border-bottom: 3px solid #d32f2f;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #1976d2;
            border-left: 4px solid #1976d2;
            padding-left: 15px;
            margin-top: 40px;
        }}
        .metric-card {{
            display: inline-block;
            background: #f5f5f5;
            padding: 20px;
            margin: 10px;
            border-radius: 8px;
            min-width: 200px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 48px;
            font-weight: bold;
            color: {risk_color};
        }}
        .metric-label {{
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
        }}
        .attack-card {{
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .attack-card.vulnerable {{
            border-left: 4px solid #d32f2f;
            background: #ffebee;
        }}
        .attack-card.not-vulnerable {{
            border-left: 4px solid #2196f3;
            background: #e3f2fd;
        }}
        .status-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 12px;
            text-transform: uppercase;
        }}
        .status-vulnerable {{
            background: #d32f2f;
            color: white;
        }}
        .status-not-vulnerable {{
            background: #2196f3;
            color: white;
        }}
        .indicators {{
            background: #fff3e0;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .code {{
            background: #263238;
            color: #aed581;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background: #1976d2;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .timestamp {{
            color: #666;
            font-size: 14px;
        }}
        .footer {{
            margin-top: 60px;
            padding-top: 20px;
            border-top: 2px solid #ddd;
            text-align: center;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 A2A Customer Service Agent Chain - Security Assessment</h1>
        <p class="timestamp">Generated: {timestamp}</p>
        
        <h2>Executive Summary</h2>
        <div style="text-align: center;">
            <div class="metric-card">
                <div class="metric-value">{successful_attacks}/{total_attacks}</div>
                <div class="metric-label">Successful Attacks</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{success_rate:.0f}%</div>
                <div class="metric-label">Vulnerability Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: {risk_color};">{risk_level}</div>
                <div class="metric-label">Risk Level</div>
            </div>
        </div>
        
        <h2>Test Scenario</h2>
        <p><strong>System Under Test:</strong> Customer Service Agent Chain</p>
        <p><strong>Architecture:</strong></p>
        <div class="code">
User Request → Customer Service Agent → Database Agent → Email Agent → Response
        </div>
        <p><strong>Objective:</strong> Assess vulnerability to prompt injection attacks in A2A communication</p>
        
        <h2>Baseline Behavior</h2>
        <div class="attack-card not-vulnerable">
            <h3>✅ Normal Operation Verified</h3>
            <p><strong>Test User:</strong> {baseline_result.get('user', 'N/A')}</p>
            <p><strong>Result:</strong> System correctly enforced authentication and authorization boundaries.</p>
            <ul>
                <li>✓ User data properly scoped to authenticated user only</li>
                <li>✓ No data leakage from other users</li>
                <li>✓ Agent chain maintained security context</li>
            </ul>
        </div>
        
        <h2>Attack Scenarios</h2>
"""
    
    # Add each attack result
    for i, attack in enumerate(attack_results, 1):
        status_class = "vulnerable" if attack.get("successful") else "not-vulnerable"
        status_badge = "status-vulnerable" if attack.get("successful") else "status-not-vulnerable"
        status_text = "VULNERABLE" if attack.get("successful") else "NOT VULNERABLE"
        status_icon = "⚠️" if attack.get("successful") else "ℹ️"
        
        indicators_html = ""
        if attack.get('indicators'):
            indicators_html = '<div class="indicators"><strong>⚠️ Vulnerability Indicators:</strong><ul>'
            for indicator in attack.get('indicators', []):
                indicators_html += f'<li>{indicator}</li>'
            indicators_html += '</ul></div>'
        
        impact_html = ""
        if attack.get('successful'):
            impact_html = f'<p><strong>Impact:</strong> {get_attack_impact(attack.get("attack_name"))}</p>'
        
        html += f"""
        <div class="attack-card {status_class}">
            <h3>{status_icon} Attack {i}: {attack.get('attack_name', 'Unknown')}</h3>
            <span class="status-badge {status_badge}">{status_text}</span>
            
            <p><strong>Attack Vector:</strong> {get_attack_description(attack.get('attack_name'))}</p>
            
            {indicators_html}
            
            {impact_html}
        </div>
"""
    
    html += f"""
        <h2>Vulnerability Summary</h2>
        <table>
            <tr>
                <th>Attack Type</th>
                <th>Status</th>
                <th>Risk Level</th>
                <th>Recommendation</th>
            </tr>
"""
    
    for attack in attack_results:
        status = "VULNERABLE" if attack.get("successful") else "NOT VULNERABLE"
        risk = "HIGH" if attack.get("successful") else "LOW"
        rec = get_recommendation(attack.get('attack_name'))
        
        html += f"""
            <tr>
                <td>{attack.get('attack_name')}</td>
                <td><span class="status-badge {'status-vulnerable' if attack.get('successful') else 'status-not-vulnerable'}">{status}</span></td>
                <td>{risk}</td>
                <td>{rec}</td>
            </tr>
"""
    
    html += """
        </table>
        
        <h2>Recommended Mitigations</h2>
        <ol>
            <li><strong>Input Sanitization:</strong> Implement strict input validation to detect and remove injection patterns</li>
            <li><strong>Context Isolation:</strong> Sanitize context passed between agents, use whitelisted fields only</li>
            <li><strong>Authentication Enforcement:</strong> Verify user identity at each agent boundary</li>
            <li><strong>Query Validation:</strong> Validate database queries to ensure user-scoped access only</li>
            <li><strong>Output Filtering:</strong> Filter responses to prevent data leakage</li>
            <li><strong>Logging & Monitoring:</strong> Implement comprehensive logging of all agent interactions</li>
            <li><strong>Anomaly Detection:</strong> Deploy behavioral analysis to detect unusual patterns</li>
        </ol>
        
        <h2>Security Best Practices for A2A Systems</h2>
        <div class="code">
# 1. Always validate user identity
def process_request(auth_user, request):
    verify_authentication(auth_user)
    verify_authorization(auth_user, request)

# 2. Sanitize inputs and context
def handoff_to_agent(context):
    safe_context = sanitize_context(context)
    validate_context_schema(safe_context)

# 3. Scope data access strictly
def query_data(user_id):
    # Only query for specific user_id
    return db.query("WHERE user_id = ?", [user_id])

# 4. Monitor for anomalies
def log_interaction(agent, user, action):
    log(agent, user, action)
    detect_anomalies(agent, user, action)
        </div>
        
        <h2>Conclusion</h2>
        <p>This security assessment reveals that A2A systems are vulnerable to sophisticated prompt injection attacks 
        if proper safeguards are not implemented. The attacks demonstrated how malicious instructions can propagate 
        through agent chains, potentially leading to:</p>
        <ul>
            <li>Unauthorized data access</li>
            <li>Privilege escalation</li>
            <li>Data exfiltration</li>
            <li>User impersonation</li>
        </ul>
        
        <p><strong>Immediate Action Required:</strong> Implement the recommended mitigations before deploying 
        A2A systems in production environments.</p>
        
        <div class="footer">
            <p><strong>⚠️ CONFIDENTIAL SECURITY ASSESSMENT</strong></p>
            <p>This report contains sensitive security information. Handle according to your organization's security policies.</p>
            <p>Generated by A2A Security POC Framework</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Save report
    os.makedirs("reports", exist_ok=True)
    report_path = os.path.join("reports", f"poc_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
    
    with open(report_path, 'w') as f:
        f.write(html)
    
    logger.success(f"HTML report generated: {report_path}")
    return report_path


def run_full_demo():
    """Run complete demonstration with all attacks"""
    
    logger.info("This demonstration will:")
    logger.step(1, 3, "Show baseline secure behavior")
    logger.step(2, 3, "Execute 4 attack scenarios")
    logger.step(3, 3, "Generate comprehensive security report")
    print()
    
    safe_input("Press Enter to start...\n")
    
    # Run baseline
    logger.section("PHASE 1: BASELINE BEHAVIOR")
    baseline_result = run_baseline_demo()
    
    # Run all attacks
    logger.section("PHASE 2: ATTACK SCENARIOS")
    
    attack_results = []
    
    # Attack 1
    result_1 = run_direct_injection_attack()
    attack_results.append(result_1)
    
    # Attack 2
    result_2 = run_context_poisoning_attack()
    attack_results.append(result_2)
    
    # Attack 3
    result_3 = run_privilege_escalation_attack()
    attack_results.append(result_3)
    
    # Attack 4
    result_4 = run_lateral_movement_attack()
    attack_results.append(result_4)
    
    # Generate report
    logger.section("PHASE 3: REPORT GENERATION")
    
    logger.info("Generating comprehensive security report...")
    report_path = generate_html_report(baseline_result, attack_results)
    
    # Save attack log
    attack_logger.save_to_file()
    
    # Summary
    logger.section("DEMONSTRATION COMPLETE")
    
    summary = attack_logger.get_summary()
    logger.info(f"Total Attacks: {summary['total_attacks']}")
    logger.info(f"Successful (Vulnerable): {summary['successful']}")
    logger.info(f"Not Vulnerable: {summary['not_vulnerable']}")
    logger.info(f"Vulnerability Rate: {summary['success_rate']}")
    
    logger.success(f"\n📊 Report saved to: {report_path}")
    logger.success("📝 Attack log saved to: reports/attack_log.json")
    
    logger.divider()
    logger.info("Thank you for using the A2A Security POC!")
    logger.info("Remember: This is for authorized security testing only.")
    
    return {
        "baseline": baseline_result,
        "attacks": attack_results,
        "report_path": report_path,
        "summary": summary
    }


if __name__ == "__main__":
    run_full_demo()

