"""
Verification script for the analyzer module.
Tests the static analysis workflow using SonarQube.
"""
import os
import sys
import json
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.analyzer import analyze_tasks
from src.sonarqube import SonarQubeAnalyzer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info("Configuration loaded successfully")
        return config
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return None

def cleanup_sonarqube():
    logger.info("Cleaning up existing SonarQube projects...")
    analyzer = SonarQubeAnalyzer()
    if analyzer.delete_all_projects():
        logger.info("Successfully cleaned up all SonarQube projects")
        return True
    else:
        logger.warning("Failed to clean up some SonarQube projects")
        return False

def main():
    logger.info("Starting analyzer verification...")
    
    cleanup_sonarqube()
    
    config = load_config()
    if not config:
        return False
    
    test_params = {
        'languages': config['languages'],
        'tasks': config['task_names'],
        'completeness_levels': config['prompt_templates']['completeness_levels'],
        'models': {model: endpoint for model, endpoint in config['api_endpoints'].items()},
        'base_output_dir': os.path.join(os.path.dirname(__file__), '..', 'codes')
    }
    
    temp_dir = os.environ.get('TEMP_DIR')
    if temp_dir:
        logger.info(f"Using temporary directory: {temp_dir}")
        test_params['temp_dir'] = temp_dir
    else:
        logger.warning("TEMP_DIR environment variable not set")
    
    logger.info("\nAnalyzing code with parameters:")
    logger.info(f"Languages: {test_params['languages']}")
    logger.info(f"Tasks: {test_params['tasks']}")
    logger.info(f"Completeness levels: {test_params['completeness_levels']}")
    logger.info(f"Models: {list(test_params['models'].keys())}")
    logger.info(f"Base output directory: {test_params['base_output_dir']}\n")
    
    success = analyze_tasks(**test_params)
    
    if success:
        logger.info("\nVerification complete. Check the results/static_analysis directory for analysis results.")
    else:
        logger.warning("\nVerification completed with some failures. Check the logs for details.")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 