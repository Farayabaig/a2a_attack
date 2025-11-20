"""
Main Entry Point for A2A Security POC
"""

import argparse
import sys
import os
from src.utils import logger
import config
from demos.demo_baseline import run_baseline_demo
from demos.demo_full import run_full_demo
from attacks.attack_1_direct_injection import run_direct_injection_attack
from attacks.attack_2_context_poisoning import run_context_poisoning_attack
from attacks.attack_3_privilege_escalation import run_privilege_escalation_attack
from attacks.attack_4_lateral_movement import run_lateral_movement_attack


def check_configuration():
    """Check and display configuration status"""
    logger.info("Checking configuration...")
    
    issues = []
    
    # Check provider
    provider = config.LLM_PROVIDER
    logger.info(f"Provider: {provider.upper()}")
    
    # Check API keys based on provider
    if provider == 'anthropic':
        if not config.ANTHROPIC_API_KEY or config.ANTHROPIC_API_KEY == 'your_anthropic_api_key_here':
            issues.append("ANTHROPIC_API_KEY not configured")
            logger.warning("⚠️  Anthropic API key not set")
        else:
            logger.success(f"✅ Anthropic API key configured ({config.ANTHROPIC_API_KEY[:10]}...)")
    
    elif provider == 'litellm':
        if not config.LITELLM_BASE_URL or config.LITELLM_BASE_URL == 'https://your-litellm-server.com':
            issues.append("LITELLM_BASE_URL not configured")
            logger.warning("⚠️  LiteLLM base URL not set")
        else:
            logger.success(f"✅ LiteLLM base URL: {config.LITELLM_BASE_URL}")
        
        if not config.LITELLM_API_KEY or config.LITELLM_API_KEY == 'your_litellm_api_key_here':
            issues.append("LITELLM_API_KEY not configured")
            logger.warning("⚠️  LiteLLM API key not set")
        else:
            logger.success(f"✅ LiteLLM API key configured")
    
    # Check model based on provider
    if provider == 'anthropic':
        model_name = config.ANTHROPIC_MODEL if config.ANTHROPIC_MODEL else config.MODEL_NAME
        logger.info(f"Anthropic Model: {model_name}")
    elif provider == 'litellm':
        model_name = config.LITELLM_MODEL if config.LITELLM_MODEL else config.MODEL_NAME
        logger.info(f"LiteLLM Model: {model_name}")
    else:
        model_name = config.MODEL_NAME
        logger.info(f"Model: {model_name}")
    logger.info(f"Max Tokens: {config.MAX_TOKENS}")
    
    # Check API calls enabled
    if not config.ENABLE_ACTUAL_API_CALLS:
        logger.warning("⚠️  API calls disabled - running in simulation mode")
    else:
        logger.success("✅ API calls enabled")
    
    if issues and config.ENABLE_ACTUAL_API_CALLS:
        logger.error("❌ Configuration issues found:")
        for issue in issues:
            logger.error(f"   - {issue}")
        logger.warning("⚠️  API calls will fail. Please check your .env file.")
        logger.info("Continuing in simulation mode...")
    else:
        logger.success("✅ Configuration looks good!")
    
    return len(issues) == 0


def main():
    """Main CLI interface"""
    
    parser = argparse.ArgumentParser(
        description="A2A Security POC - Agent-to-Agent Security Testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                    # Run full demonstration
  python run.py --baseline         # Run baseline only
  python run.py --attack 1         # Run attack 1 only
  python run.py --attack all       # Run all attacks
        """
    )
    
    parser.add_argument(
        '--baseline',
        action='store_true',
        help='Run baseline demonstration only'
    )
    
    parser.add_argument(
        '--attack',
        type=str,
        choices=['1', '2', '3', '4', 'all'],
        help='Run specific attack (1-4) or all attacks'
    )
    
    parser.add_argument(
        '--full',
        action='store_true',
        help='Run full demonstration (baseline + all attacks + report)'
    )
    
    args = parser.parse_args()
    
    # Display banner
    print("\n" + "="*80)
    print(" " * 20 + "A2A Security POC")
    print(" " * 15 + "Agent-to-Agent Security Testing")
    print("="*80 + "\n")
    
    logger.warning("⚠️  AUTHORIZED SECURITY TESTING ONLY")
    logger.info("This tool is for educational and authorized testing purposes.")
    
    # Check configuration
    check_configuration()
    
    logger.divider()
    
    try:
        if args.baseline:
            logger.section("Running Baseline Demonstration")
            run_baseline_demo()
        
        elif args.attack:
            logger.section(f"Running Attack {args.attack}")
            if args.attack == '1':
                run_direct_injection_attack()
            elif args.attack == '2':
                run_context_poisoning_attack()
            elif args.attack == '3':
                run_privilege_escalation_attack()
            elif args.attack == '4':
                run_lateral_movement_attack()
            elif args.attack == 'all':
                logger.info("Running all 4 attack scenarios...")
                run_direct_injection_attack()
                run_context_poisoning_attack()
                run_privilege_escalation_attack()
                run_lateral_movement_attack()
        
        elif args.full:
            logger.section("Running Full Demonstration")
            run_full_demo()
        
        else:
            # Default: run full demo
            logger.section("Running Full Demonstration")
            run_full_demo()
        
        logger.divider()
        logger.success("✅ Execution completed successfully!")
        logger.info("Check the reports/ directory for generated reports.")
    
    except KeyboardInterrupt:
        logger.warning("⚠️  Execution interrupted by user.")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"❌ Error during execution: {e}")
        logger.error("Please check your configuration and try again.")
        if config.VERBOSE_LOGGING:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

