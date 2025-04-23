"""
Test Manager Module:
Manages test execution and evaluation of generated code.
"""
import os
import json
import jsonlines
import time
from datetime import datetime
from typing import Dict, Any
from src.runner import run_code


def load_test_cases(task_name: str) -> Dict[str, Any]:
    """Load test cases for a specific task."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_file = os.path.join(base_dir, 'test_cases', f'{task_name}_test_cases.json')
    with open(test_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_input_data(task_name: str, case: Dict[str, Any] = None, test_cases_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Load and process input data for a specific task.
    
    Args:
        task_name (str): Name of the task
        case (Dict[str, Any], optional): Current test case data
        test_cases_data (Dict[str, Any], optional): All test cases data
        
    Returns:
        Dict[str, Any]: Processed input data ready for use
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_file = os.path.join(base_dir, 'test_cases', 'input_data.json')
    
    with open(input_file, 'r', encoding='utf-8') as f:
        input_templates = json.load(f)
    
    if case is None and test_cases_data is None:
        return input_templates
    
    template = input_templates.get(task_name, {})
    
    # eval input_data.json
    local_vars = {}
    if case:
        local_vars['case'] = case
    if test_cases_data:
        local_vars['test_cases'] = test_cases_data
    

    result = {}
    for key, value in template.items():
        if isinstance(value, str) and ('case' in value or 'test_cases' in value):
            try:
                result[key] = eval(value, {"__builtins__": {}}, local_vars)
            except:
                result[key] = value
        else:
            result[key] = value
    
    return result

def get_task_components(file_path: str, language: str) -> str:
    """Extract task components from file path to create task_id.
    
    Args:
        file_path (str): Path to the code file
        language (str): Programming language
        
    Returns:
        str: task_id in format {language}_{model}_{completeness}_{task_name}
    """
    normalized_path = file_path.replace('\\', '/').replace('//', '/')
    parts = normalized_path.split('/')
    
    try:
        lang_idx = parts.index(language)
        model = parts[lang_idx + 1].lower() 
        completeness = parts[lang_idx + 2]
        task_name = parts[lang_idx + 3]  
        
        return f"{language}_{model}_{completeness}_{task_name}"
    except (ValueError, IndexError):
        print(f"Warning: Could not parse path components from {file_path}")
        return f"{language}_unknown_unknown_{task_name}"


def extract_key_error(error_message: str) -> str:
    """Extract key error message from a potentially long error output.
    
    Args:
        error_message (str): Original error message
        
    Returns:
        str: Extracted key error message
    """
    if not error_message:
        return ""
        
    lines = [line.strip() for line in error_message.split('\n') if line.strip()]
    
    if "error:" in error_message.lower():
        for line in lines:
            if "error:" in line.lower():
                return line.strip()
    
    for line in reversed(lines):
        # Skip traceback lines
        if line.startswith('  File "') or line.startswith('    '):
            continue
        return line.strip()
    
    return lines[-1] if lines else error_message[:200]


def execute_task(file_path: str, language: str, task_name: str) -> Dict[str, Any]:
    """Execute all test cases for task 1 and record overall execution results.
    
    Args:
        file_path (str): Path to the code file
        language (str): Programming language of the code
        
    Returns:
        Dict[str, Any]: Execution results for execution.ndjson
    """
    test_cases = load_test_cases(task_name)
    retry_count = 0
    max_retries = 1
    task_id = get_task_components(file_path, language)
    last_error_type = None
    last_error_message = None
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(os.path.join(base_dir, 'results', 'execution'), exist_ok=True)
    
    while retry_count < max_retries:
        try:
            case = test_cases['test_cases'][0]
            
            input_data = load_input_data(task_name, case, test_cases)
                    
            result = run_code(file_path, language, input_data=json.dumps(input_data))
            
            execution_result = {
                'task_id': task_id,
                'execution_status': 'success' if result['success'] else 'failure',
                'error_type': result.get('error_type'),
                'error_message': extract_key_error(result.get('error_message', '')),
                'retry_count': retry_count,
                'exit_code': result.get('exit_code', -1),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Save each attempt to execution.ndjson
            execution_file = os.path.join(base_dir, 'results', 'execution', f'{task_name}.ndjson')
            with jsonlines.open(execution_file, mode='a') as writer:
                writer.write(execution_result)
            
            if result['success']:
                return execution_result
                
            last_error_type = result.get('error_type')
            last_error_message = result.get('error_message')
            
        except Exception as e:
            error_type = type(e).__name__
            error_message = str(e)
            
            execution_result = {
                'task_id': task_id,
                'execution_status': 'failure',
                'error_type': error_type,
                'error_message': extract_key_error(error_message),
                'retry_count': retry_count,
                'exit_code': -1,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            execution_file = os.path.join(base_dir, 'results', 'execution', f'{task_name}.ndjson')
            with jsonlines.open(execution_file, mode='a') as writer:
                writer.write(execution_result)
            
            last_error_type = error_type
            last_error_message = error_message
            
        retry_count += 1
        if retry_count < max_retries:
            time.sleep(1)  
    
    # If all retries failed, return the last failure result
    return {
        'task_id': task_id,
        'execution_status': 'failure',
        'error_type': last_error_type,
        'error_message': extract_key_error(last_error_message) if last_error_message else None,
        'retry_count': retry_count,
        'exit_code': -1,
        'timestamp': datetime.utcnow().isoformat()
    }


def test_task(file_path: str, language: str, task_name: str) -> None:
    """Run all test cases for task 1 and record test results.
    
    Args:
        file_path (str): Path to the code file
        language (str): Programming language of the code
        task_name (str): Name of the task
    """
    test_cases = load_test_cases(task_name=task_name)
    task_id = get_task_components(file_path, language)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for case in test_cases['test_cases']:
        input_data = load_input_data(task_name, case, test_cases)
        
        result = run_code(file_path, language, input_data=json.dumps(input_data))
        
        test_result = {
            'task_id': task_id,
            'test_case_id': str(case['test_case']),
            'expected_output': case['expected_result'],
            'actual_output': extract_key_error(result.get('error_message', '')),
            'test_passed': False,
            'execution_duration': result.get('duration', 0.0),
            'memory_usage': result.get('resources', {}).get('memory_usage', 0.0),
            'cpu_time': result.get('resources', {}).get('cpu_time', 0.0),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if result['success']:
            try:
                actual_output = json.loads(result['stdout'])
                if not isinstance(actual_output, dict):
                    test_result['actual_output'] = f"Invalid output format: expected object, got {type(actual_output)}"
                else:
                    test_result['actual_output'] = actual_output
                    test_result['test_passed'] = actual_output == case['expected_result']
            except json.JSONDecodeError:
                test_result['actual_output'] = f"Invalid JSON output: {result['stdout'][:100]}"
        
        os.makedirs(os.path.join(base_dir, 'results', 'test_results'), exist_ok=True)
        test_results_file = os.path.join(base_dir, 'results', 'test_results', f'{task_name}.ndjson')
        with jsonlines.open(test_results_file, mode='a') as writer:
            writer.write(test_result)
