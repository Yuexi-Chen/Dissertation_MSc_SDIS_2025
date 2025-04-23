import os
import json
import logging
from datetime import datetime
from pathlib import Path
from src.sonarqube import SonarQubeAnalyzer, DEFAULT_TEMP_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results')

STATIC_ANALYSIS_DIR = os.path.join(BASE_RESULTS_DIR, 'static_analysis')
os.makedirs(STATIC_ANALYSIS_DIR, exist_ok=True)

STATIC_ANALYSIS_FILE = os.path.join(STATIC_ANALYSIS_DIR, '{task_name}.ndjson')

def analyze_code(codes_dir=None, language=None, model=None, prompt_type=None, task_name=None, temp_dir=DEFAULT_TEMP_DIR):
    """
    Analyze code using SonarQube and save results to NDJSON file
    
    Args:
        codes_dir: Directory containing code files (default: 'codes')
        language: Programming language to analyze (default: all)
        model: Model name to analyze (default: all)
        prompt_type: Prompt type to analyze (default: all)
        task_name: Task name to analyze (e.g., 'task_1', 'task_2') (default: all)
        temp_dir: Temporary directory for SonarQube analysis
        
    Returns:
        bool: True if analysis was successful, False otherwise
    """
    if codes_dir is None:
        codes_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'codes')
    
    analyzer = SonarQubeAnalyzer(temp_dir=temp_dir)
    if not analyzer.authenticate():
        logger.error("Failed to authenticate with SonarQube. Aborting analysis.")
        return False
    
    code_files = find_code_files(codes_dir, language, model, prompt_type, task_name)
    if not code_files:
        logger.warning(f"No code files found to analyze in {codes_dir}")
        return False
    
    logger.info(f"Found {len(code_files)} code files to analyze")
    
    success_count = 0
    for file_path in code_files:
        if analyze_file(analyzer, file_path, task_name, temp_dir):
            success_count += 1
    
    logger.info(f"Successfully analyzed {success_count} out of {len(code_files)} files")
    return success_count > 0

def find_code_files(codes_dir, language=None, model=None, prompt_type=None, task_name=None):
    """
    Find code files to analyze based on filters
    
    Args:
        codes_dir: Directory containing code files
        language: Programming language to analyze
        model: Model name to analyze
        prompt_type: Prompt type to analyze
        task_name: Task name to analyze (e.g., 'task_1', 'task_2')
    
    Returns:
        List of file paths to analyze
    """
    files = []
    
    if task_name:
        task_folder = task_name if task_name.startswith('task_') else f'task_{task_name}'
    else:
        task_folder = None
    
    for file in Path(codes_dir).rglob('Solution.*'):
        try:
            path_parts = file.parts
            
            # Expected path structure: codes/language/model/prompt_type/task_x/Solution.*
            # So counting from the end: -1 is Solution.*, -2 is task_x, -3 is prompt_type, etc.
            
            # Check each path component matches the filter
            if language and language.lower() != path_parts[-5].lower():
                continue
            if model and model.lower() != path_parts[-4].lower():
                continue
            if prompt_type and prompt_type.lower() != path_parts[-3].lower():
                continue
            if task_folder and task_folder.lower() != path_parts[-2].lower():
                continue
                
            files.append(str(file))
            
        except IndexError:
            continue
    
    logger.info(f"Found {len(files)} matching files")
    return files

def analyze_file(analyzer, file_path, specified_task_name=None, temp_dir=None):
    """
    Analyze a single code file using SonarQube
    
    Args:
        analyzer: SonarQubeAnalyzer instance
        file_path: Path to the code file
        specified_task_name: Task name specified by the user (for output file naming)
        temp_dir: Temporary directory for SonarQube analysis
        
    Returns:
        bool: True if analysis was successful, False otherwise
    """
    # Extract information from file path
    # Expected format: codes/{language}/{model}/{prompt_type}/task_{task_name}/Solution.*
    try:
        path_parts = Path(file_path).parts
        task_folder = [part for part in path_parts if part.startswith('task_')][-1] 
        task_name = task_folder  
        
        language_idx = -5 if len(path_parts) >= 5 else -1
        model_idx = -4 if len(path_parts) >= 4 else -1
        prompt_type_idx = -3 if len(path_parts) >= 3 else -1
        
        language = path_parts[language_idx] if language_idx >= -len(path_parts) else "unknown"
        model = path_parts[model_idx] if model_idx >= -len(path_parts) else "unknown"
        prompt_type = path_parts[prompt_type_idx] if prompt_type_idx >= -len(path_parts) else "unknown"
        
        logger.info(f"Extracted file info: language={language}, model={model}, prompt_type={prompt_type}, task_name={task_name}")
    except (IndexError, ValueError) as e:
        logger.error(f"Could not extract task information from file path: {file_path}. Error: {str(e)}")
        return False
    
    # Create a unique project key for SonarQube (this is the full identifier)
    project_key = f"{language}_{model}_{prompt_type}_{task_folder}"
    project_name = f"{language} {model} {prompt_type} {task_folder}"
    
    logger.info(f"Analyzing {file_path} (Project: {project_key})")
    
    # Create project in SonarQube
    if not analyzer.create_project(project_key, project_name):
        logger.warning(f"Failed to create SonarQube project for {file_path}")
        return False
    
    if not analyzer.run_analysis(project_key, file_path, temp_dir):
        logger.warning(f"Failed to run SonarQube analysis for {file_path}")
        return False
    
    measures = analyzer.get_measures(project_key)
    if not measures:
        logger.warning(f"Failed to get SonarQube measures for {file_path}")
        return False
    
    issues = analyzer.get_issues(project_key)
    if issues is None:
        logger.warning(f"Failed to get SonarQube issues for {file_path}")
        issues = []
    
    relative_path = file_path
    codes_index = file_path.find('codes')
    if codes_index != -1:
        relative_path = file_path[codes_index:]
    
    result = {
        "task_id": project_key.lower(),  # Full identifier
        "task_name": task_name,  # Keep the full "task_X" format
        "language": language,
        "model": model,
        "prompt_type": prompt_type,
        "file_path": relative_path,
        "cyclomatic_complexity": float(measures.get('complexity', 0)),
        "cognitive_complexity": float(measures.get('cognitive_complexity', 0)),
        "comment_coverage": float(measures.get('comment_lines_density', 0)),
        "code_redundancy": float(measures.get('duplicated_lines_density', 0)),
        "file_line_count": int(measures.get('ncloc', 0)),
        "maintainability_rating": float(measures.get('sqale_rating', 0)),
        "technical_debt": float(measures.get('sqale_index', 0)),
        "bugs": int(measures.get('bugs', 0)),
        "vulnerabilities": int(measures.get('vulnerabilities', 0)),
        "code_smells": int(measures.get('code_smells', 0)),
        "security_rating": float(measures.get('security_rating', 0)),
        "reliability_rating": float(measures.get('reliability_rating', 0)),
        "timestamp": datetime.now().isoformat()
    }
    
    # issues summary
    if issues:
        issues_summary = {
            "total": len(issues),
            "by_severity": {},
            "by_type": {}
        }
        
        for issue in issues:
            severity = issue.get('severity', 'UNKNOWN')
            issue_type = issue.get('type', 'UNKNOWN')
            
            if severity not in issues_summary["by_severity"]:
                issues_summary["by_severity"][severity] = 0
            issues_summary["by_severity"][severity] += 1
            
            if issue_type not in issues_summary["by_type"]:
                issues_summary["by_type"][issue_type] = 0
            issues_summary["by_type"][issue_type] += 1
        
        result["issues"] = issues_summary
    
    output_task_name = specified_task_name if specified_task_name else task_name
    
    if output_task_name and not output_task_name.startswith('task_'):
        output_task_name = f"task_{output_task_name}"
    
    output_file = STATIC_ANALYSIS_FILE.format(task_name=output_task_name)
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(result) + '\n')
    
    logger.info(f"Analysis completed for {file_path}, results saved to {output_file}")
    return True

def test_sonarqube():
    """
    Test SonarQube connection and API functionality
    """
    from src.sonarqube import test_sonarqube_connection
    return test_sonarqube_connection()

def analyze_tasks(languages=None, tasks=None, completeness_levels=None, models=None, base_output_dir='codes', temp_dir=DEFAULT_TEMP_DIR):
    """
    Analyze code for multiple tasks, languages, models, and completeness levels
    
    Args:
        languages: List of programming languages to analyze
        tasks: List of tasks to analyze (e.g., ['task_1', 'task_2'])
        completeness_levels: List of prompt types to analyze
        models: Dictionary of models to analyze (keys are model names)
        base_output_dir: Base directory containing code files
        temp_dir: Temporary directory for SonarQube analysis
        
    Returns:
        bool: True if all analyses were successful, False otherwise
    """
    logger.info("Starting code analysis...")
    
    overall_success = True
    
    if tasks is None:
        tasks = ['task_1']
    
    # Analyze each task
    for task in tasks:
        logger.info(f"Analyzing task: {task}")
        
        task_name = task if task.startswith('task_') else f"task_{task}"
        
        task_success = analyze_code(
            codes_dir=base_output_dir,
            language=languages[0] if languages and len(languages) == 1 else None,
            model=list(models.keys())[0] if models and len(models) == 1 else None,
            prompt_type=completeness_levels[0] if completeness_levels and len(completeness_levels) == 1 else None,
            task_name=task_name,
            temp_dir=temp_dir
        )
        
        if task_success:
            logger.info(f"Analysis for {task_name} completed successfully")
        else:
            logger.error(f"Analysis for {task_name} failed")
            overall_success = False
    
    if overall_success:
        logger.info("All analyses completed successfully")
    else:
        logger.warning("Some analyses failed")
    
    return overall_success

if __name__ == '__main__':
    # Test SonarQube connection
    if test_sonarqube():
        analyze_code(task_name="task_1")
    else:
        logger.error("SonarQube connection test failed. Please check the configuration.")
