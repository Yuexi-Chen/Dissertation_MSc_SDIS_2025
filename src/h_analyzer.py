import os
import json
from datetime import datetime
import logging

def generate_explicit_hallucinations(execution_data):
    if execution_data["execution_status"] != "failure":
        return {
            "nonexistent_library": False,
            "undefined_function": False, 
            "invalid_api_usage": False,
            "syntax_error": False
        }
    
    error_msg = execution_data["error_message"].lower() if execution_data["error_message"] else ""
    error_type = execution_data["error_type"]
    
    return {
        
        "nonexistent_library": any(pattern in error_msg for pattern in 
                                ["imported and not used", "no module named", "cannot find module"]) or error_type == "ImportError",
        
        
        "undefined_function": any(pattern in error_msg for pattern in 
                               ["undefined", "not defined", "name", "reference", "is not defined", "cannot read properties of undefined"]) or error_type in ["NameError", "ReferenceError"],
        
        
        "invalid_api_usage": (
            (error_type == "TypeError" and "undefined" not in error_msg) or
            
            any(pattern in error_msg for pattern in [
                "argument", 
                "method",    
                "function",  
                "property",  
                "assignment to constant",  
                "immutable",  
                "invalid"    
            ])
        ),
        
        
        "syntax_error": "syntax" in error_msg or error_type == "SyntaxError"
    }

def load_execution_data(task_id, task_name):
    execution_file = os.path.join("results", "execution", f"{task_name}.ndjson")
    
    if not os.path.exists(execution_file):
        return {"execution_status": "unknown", "error_message": "", "error_type": None}
    
    with open(execution_file, "r") as f:
        for line in f:
            data = json.loads(line)
            if data["task_id"] == task_id:
                return data
    
    return {"execution_status": "unknown", "error_message": "", "error_type": None}

def load_test_results_data(task_id, task_name):
    test_results_file = os.path.join("results", "test_results", f"{task_name}.ndjson")
    
    if not os.path.exists(test_results_file):
        return []
    
    results = []
    with open(test_results_file, "r") as f:
        for line in f:
            data = json.loads(line)
            if data["task_id"] == task_id:
                results.append(data)
    
    return results

def process_all_tasks(target_languages=None, target_tasks=None, target_prompt_types=None, target_models=None):
    """
    Process hallucination analysis for specified tasks, controlled by config.json
    
    Args:
        target_languages (list): List of languages to process
        target_tasks (list): List of tasks to process
        target_prompt_types (list): List of prompt types to process
        target_models (list): List of models to process
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    os.makedirs(os.path.join("results", "hallucination"), exist_ok=True)
    
    if not target_tasks:
        logger.error("No tasks specified in config.json!")
        return False
    
    logger.info(f"Will process tasks: {target_tasks}")
    logger.info(f"Filtering by languages: {target_languages}")
    logger.info(f"Filtering by prompt types: {target_prompt_types}")
    logger.info(f"Filtering by models: {target_models}")
    
    total_processed = 0
    
    for task_name in target_tasks:
        output_file = os.path.join("results", "hallucination", f"{task_name}.ndjson")
        logger.info(f"Processing task: {task_name}")
        
        combinations = []
        for language in target_languages:
            for model in target_models:
                for prompt_type in target_prompt_types:
                    task_id = f"{language}_{model}_{prompt_type}_{task_name}"
                    combinations.append({
                        "task_id": task_id,
                        "task_name": task_name,
                        "language": language,
                        "model": model,
                        "prompt_type": prompt_type
                    })
        
        processed_count = 0
        with open(output_file, "w") as f:
            for task in combinations:
                task_id = task["task_id"]
                language = task["language"]
                model = task["model"]
                prompt_type = task["prompt_type"]
                
                if not check_generation_exists(task_id, task_name):
                    logger.warning(f"No generation record for {task_id}, skipping")
                    continue
                
                execution_data = load_execution_data(task_id, task_name)
                
                test_results_data = load_test_results_data(task_id, task_name)
                
                explicit_hallucinations = generate_explicit_hallucinations(execution_data)
                
                test_passed_count = sum(1 for test in test_results_data if test.get("test_passed", False))
                test_total_count = len(test_results_data)
                
                hallucination_result = {
                    "task_id": task_id,
                    "task_name": task_name,
                    "language": language,
                    "model": model,
                    "prompt_type": prompt_type,
                    "explicit_hallucinations": explicit_hallucinations,
                    "test_passed_count": test_passed_count,
                    "test_total_count": test_total_count,
                    "timestamp": datetime.now().isoformat()
                }
                
                f.write(json.dumps(hallucination_result) + "\n")
                processed_count += 1
                total_processed += 1
        
        logger.info(f"Processed {processed_count} combinations for task {task_name}")
    
    logger.info(f"Hallucination analysis completed. Processed {total_processed} tasks.")
    return total_processed > 0

def check_generation_exists(task_id, task_name):
    generation_file = os.path.join("results", "generation", f"{task_name}.ndjson")
    
    if not os.path.exists(generation_file):
        return False
    
    try:
        with open(generation_file, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get("task_id") == task_id:
                        return True
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
    
    return False



    