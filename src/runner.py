"""
Runner module: Responsible for executing generated code.
Handles runtime execution and captures outputs/errors.
"""
import time
import json
import psutil
import subprocess
from typing import Optional, List, Dict, Any, Tuple

def get_resource_usage(process):
    try:
        with process.oneshot():
            cpu_time = sum(process.cpu_times()[:2])  # user + system time
            memory_info = process.memory_info()
            return {
                'cpu_time': cpu_time,
                'memory_usage': memory_info.rss / (1024 * 1024),  # Convert to MB
                'peak_memory_usage': memory_info.peak_wset / (1024 * 1024) if hasattr(memory_info, 'peak_wset') else 0
            }
    except:
        return {
            'cpu_time': 0,
            'memory_usage': 0,
            'peak_memory_usage': 0
        }


def compile_code(file_path: str, language: str) -> Tuple[bool, str, Optional[str]]:
    """Compile code if needed."""
    if language == 'python':
        return True, file_path, None
    elif language == 'javascript':
        return True, file_path, None
    elif language == 'go':
        return True, file_path, None
    
    else:
        return False, "", f"Unsupported language: {language}"


def parse_error_type(stderr: str, language: str) -> str:
    """Parse error type from stderr based on language.
    
    Args:
        stderr (str): Error message from stderr
        language (str): Programming language
        
    Returns:
        str: Error type string
    """
    if not stderr:
        return "RuntimeError"
        
    stderr_lower = stderr.lower()
    
    if language == 'javascript':
        if "referenceerror" in stderr_lower:
            return "ReferenceError"
        elif "typeerror" in stderr_lower:
            return "TypeError"
        elif "syntaxerror" in stderr_lower:
            return "SyntaxError"
        elif "import" in stderr_lower and "not found" in stderr_lower:
            return "ImportError"
        elif "cannot find module" in stderr_lower:
            return "ImportError"
    elif language == 'go':
        if "compilation error" in stderr_lower:
            return "CompilationError"
        elif "undefined" in stderr_lower:
            return "NameError"
        elif "type" in stderr_lower and "error" in stderr_lower:
            return "TypeError"
        elif "syntax error" in stderr_lower:
            return "SyntaxError"
        elif "imported and not used" in stderr_lower:
            return "ImportError"
    
    return "RuntimeError"


def run_code(file_path: str, language: str, args: Optional[List[str]] = None, input_data: Optional[str] = None, timeout: int = 30) -> Dict[str, Any]:
    """Execute generated code and capture results.
    
    Args:
        file_path (str): Path to the code file to execute
        language (str): Programming language of the code
        args (List[str], optional): Command line arguments to pass to the program
        input_data (str, optional): Input data to pass via stdin
        timeout (int): Maximum execution time in seconds
        
    Returns:
        dict: Basic execution results including stdout for testing purposes
    """
    start_time = time.time()
    args = args or []
    
    try:
        success, executable_path, error_msg = compile_code(file_path, language)
        if not success:
            return {
                'success': False,
                'error_type': 'CompilationError',
                'error_message': error_msg,
                'duration': time.time() - start_time,
                'stdout': '',
                'stderr': error_msg
            }
        
        if language == 'javascript':
            process = subprocess.Popen(
                ['node', executable_path],
                stdin=subprocess.PIPE if input_data else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        elif language == 'go':
            process = subprocess.Popen(
                ['go', 'run', executable_path],
                stdin=subprocess.PIPE if input_data else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        else: 
            process = subprocess.Popen(
                ['python', executable_path],
                stdin=subprocess.PIPE if input_data else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        
        try:
            resources = get_resource_usage(psutil.Process(process.pid))
        except:
            resources = {
                'cpu_time': 0,
                'memory_usage': 0,
                'peak_memory_usage': 0
            }
        
        stdout, stderr = process.communicate(input=input_data, timeout=timeout)
            
        error_type = None
        if process.returncode != 0:
            error_type = parse_error_type(stderr, language)
            
        return {
            'success': process.returncode == 0,
            'error_type': error_type,
            'error_message': stderr if stderr else None,
            'duration': time.time() - start_time,
            'stdout': stdout,
            'stderr': stderr,
            'exit_code': process.returncode,
            'resources': resources
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error_type': 'TimeoutError',
            'error_message': f'Execution timed out after {timeout} seconds',
            'duration': timeout,
            'stdout': '',
            'stderr': f'Execution timed out after {timeout} seconds',
            'exit_code': -1,
            'resources': {'cpu_time': 0, 'memory_usage': 0, 'peak_memory_usage': 0}
        }
    
    except Exception as e:
        return {
            'success': False,
            'error_type': type(e).__name__,
            'error_message': str(e),
            'duration': time.time() - start_time,
            'stdout': '',
            'stderr': str(e),
            'exit_code': -1,
            'resources': {'cpu_time': 0, 'memory_usage': 0, 'peak_memory_usage': 0}
        }


if __name__ == '__main__':
    # test usage with input data
    test_input = {
        "patient": {
            "id": "P001",
            "gender": "Male",
            "age": 46,
            "condition": "Orthopedic"
        },
        "ward": {
            "name": "Orthopedic Ward",
            "gender_restriction": "Male Only",
            "age_range": [16, 120]
        }
    }
    
    result = run_code(
        file_path='codes/python/Gemini/complete/task_1/Solution.py',
        language='python',
        args=['--input', json.dumps(test_input)]
    )
    print(json.dumps(result, indent=2))
