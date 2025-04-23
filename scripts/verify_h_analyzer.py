"""
Verification script for the h_analyzer module.
Tests the hallucination analysis workflow.
"""
import os
import sys
import json
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src import h_analyzer

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
    logger.info("Starting hallucination analyzer verification...")
    
    config = load_config()
    if not config:
        return False
    
    os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'results', 'hallucination'), exist_ok=True)
    
  
    analysis_params = {
        'languages': config['languages'],
        'tasks': config['task_names'],
        'completeness_levels': config['prompt_templates']['completeness_levels'],
        'models': list(config['api_endpoints'].keys())
    }
    
    logger.info("\nAnalyzing hallucinations with parameters:")
    logger.info(f"Languages: {analysis_params['languages']}")
    logger.info(f"Tasks: {analysis_params['tasks']}")
    logger.info(f"Completeness levels: {analysis_params['completeness_levels']}")
    logger.info(f"Models: {analysis_params['models']}")
    
  
    try:
        h_analyzer.process_all_tasks(
            target_languages=analysis_params['languages'],
            target_tasks=analysis_params['tasks'],
            target_prompt_types=analysis_params['completeness_levels'],
            target_models=analysis_params['models']
        )
        success = True
    except Exception as e:
        logger.error(f"Error during hallucination analysis: {str(e)}")
        success = False
    
    if success:
        logger.info("\nVerification complete. Check the results/hallucination directory for analysis results.")
    else:
        logger.warning("\nVerification completed with some failures. Check the logs for details.")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)