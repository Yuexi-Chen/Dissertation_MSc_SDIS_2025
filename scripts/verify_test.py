import os
import sys
import glob
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.test_manager import execute_task, test_task

def load_config():
    config_path = os.path.join(BASE_DIR, 'config', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def verify_test():
    print(f"Starting verification at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    config = load_config()
    
    tasks = config.get('task_names', [])
    languages = config.get('languages', [])
    models = list(config.get('api_endpoints', {}).keys())
    completeness_levels = config.get('prompt_templates', {}).get('completeness_levels', [])
    
    print(f"Configuration loaded:")
    print(f"- Tasks: {tasks}")
    print(f"- Languages: {languages}")
    print(f"- Models: {models}")
    print(f"- Completeness levels: {completeness_levels}")
    
    language_extensions = {
        'python': '.py',
        'javascript': '.js',
        'go': '.go'
    }
    
    results_dir = os.path.join(BASE_DIR, 'results')
    os.makedirs(os.path.join(results_dir, 'execution'), exist_ok=True)
    os.makedirs(os.path.join(results_dir, 'test_results'), exist_ok=True)
    
    for task_name in tasks:
        print(f"\n=== Testing task: {task_name} ===")
        
        for language in languages:
            if language not in language_extensions:
                print(f"Warning: Unsupported language {language}, skipping")
                continue
                
            ext = language_extensions[language]
            
            for model in models:
                for completeness in completeness_levels:
                    pattern = os.path.join(
                        BASE_DIR, 
                        'codes', 
                        language, 
                        model.lower(), 
                        completeness, 
                        task_name, 
                        f'Solution{ext}'
                    )
                    pattern = pattern.replace('\\', '/')
                    
                    found_files = glob.glob(pattern)
                    if not found_files:
                        print(f"Warning: No {language} file found for {model}/{completeness}/{task_name}")
                        continue
                    
                    file_path = found_files[0]
                    print(f"\nTesting {file_path}")
                    
                    try:
                        # First execute the task
                        execution_result = execute_task(file_path, language, task_name)
                        print(f"Execution result: {execution_result['execution_status']}")
                        
                        # Then run all test cases
                        test_task(file_path, language, task_name)
                        print(f"Test results have been saved")
                        
                    except Exception as e:
                        print(f"Error testing {file_path}: {str(e)}")
                        continue
    
    print(f"\nVerification completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    verify_test() 
    