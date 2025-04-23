"""
Verification script for the generator module.
Tests the code generation workflow using configured AI APIs.
"""
import os
import sys
import json
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src import generator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from config.json file."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info("Configuration loaded successfully")
        return config
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return None

def main():
    logger.info("Starting generator verification...")
    
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
    
    logger.info("\nGenerating code with parameters:")
    logger.info(f"Languages: {test_params['languages']}")
    logger.info(f"Tasks: {test_params['tasks']}")
    logger.info(f"Completeness levels: {test_params['completeness_levels']}")
    logger.info(f"Models: {list(test_params['models'].keys())}")
    logger.info(f"Base output directory: {test_params['base_output_dir']}\n")
    
    try:
        generator.generate_code(**test_params)
        success = True
    except Exception as e:
        logger.error(f"Error during code generation: {str(e)}")
        success = False
    
    if success:
        logger.info("\nVerification complete. Check the codes/ directory for generated files.")
    else:
        logger.warning("\nVerification completed with some failures. Check the logs for details.")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 