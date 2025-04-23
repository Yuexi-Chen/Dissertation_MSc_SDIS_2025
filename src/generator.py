"""
Generator Module:
Assembles prompt templates from JSON components and generates code using configured AI APIs.
Templates are assembled by combining language-specific JSONs with task JSONs of different completeness levels.
"""
import os
import json
import google.generativeai as genai
from datetime import datetime
import jsonlines


def load_config():
    with open(os.path.join('config', 'config.json'), 'r', encoding='utf-8') as f:
        return json.load(f)


def assemble_prompt(language_json, task_json):
    combined = {**language_json, **task_json}  # Simple merge for now
    return json.dumps(combined)


def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def api_call(prompt, api_key, model_name="gemini"):
    """Performs an API call to generate code using the provided prompt.
    
    Args:
        prompt (str): The assembled prompt for code generation
        api_key (str): The API key for authentication
        model_name (str): The name of the model to use:
                         - gemini: Google's Gemini models
                         - gpt: OpenAI's GPT models
                         - claude: Anthropic's Claude models
        
    Returns:
        str: The generated code with code block markers removed
    """
    model_name = model_name.lower() 
    
    if model_name == "gemini":
        genai.configure(api_key=api_key)
        
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        
        try:
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",  
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            response = model.generate_content(prompt)
            if not response.text:
                raise Exception("Empty response from API")
                
            Solution = response.text.strip()
            
        except Exception as e:
            raise Exception(f"API call failed: {str(e)}")
            
    elif model_name == "gpt":
        try:
            
            from openai import OpenAI
            
            client = OpenAI(api_key=api_key)
            
            completion = client.chat.completions.create(
                model="gpt-4o",  
                messages=[
                    {"role": "system", "content": "You are a helpful coding assistant. Generate code based on the given requirements."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4096
            )
            
            Solution = completion.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"API call failed: {str(e)}")
            
    elif model_name == "claude":
        try:
            from anthropic import Anthropic
            
            client = Anthropic(api_key=api_key)
            
            message = client.messages.create(
                model="claude-3-5-sonnet-20240620",  
                max_tokens=8192,
                temperature=0.7,
                system="You are a helpful coding assistant. Generate code based on the given requirements and only return the code.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            Solution = message.content[0].text.strip()
            
        except Exception as e:
            raise Exception(f"API call failed: {str(e)}")
    else:
        raise ValueError(f"Unsupported model: {model_name}")
        
    if Solution.startswith('```'):
        lines = Solution.split('\n')
        Solution = '\n'.join(lines[1:-1])
        
    return Solution


def save_Solution(code, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(code)


def save_generation_metadata(task_name, metadata_list):
    """Saves generation metadata to a NDJSON file.
    
    Args:
        task_name (str): Name of the task (e.g., 'task_1')
        metadata_list (list): List of metadata dictionaries to save
    """
    output_dir = os.path.join('results', 'generation')
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f'{task_name}.ndjson')
    with jsonlines.open(output_file, mode='w') as writer:
        writer.write_all(metadata_list)


def generate_code(
    languages=None,
    tasks=None,
    completeness_levels=None,
    models=None,
    base_output_dir='codes'
):
    """Main function to generate code based on specified parameters.
    
    Args:
        languages (list): List of languages to generate code for. If None, uses all languages from config.
        tasks (list): List of tasks to generate code for. If None, uses all tasks from config.
        completeness_levels (list): List of completeness levels. If None, uses all levels from config.
        models (dict): Dictionary of model names and their API endpoints. If None, uses all from config.
        base_output_dir (str): Base directory for output code files.
    """
    config = load_config()
    templates = config['prompt_templates']
    
    # Use provided parameters or defaults from config
    languages = languages or config['languages']
    tasks = tasks or config['task_names']
    completeness_levels = completeness_levels or templates['completeness_levels']
    models = models or config['api_endpoints']
    
    task_metadata = {}
    
    for language in languages:
        lang_template_path = os.path.join(templates['languages_path'], f"{language}.json")
        lang_json = load_json_file(lang_template_path)
        
        for task in tasks:
            if task not in task_metadata:
                task_metadata[task] = []
                
            task_dir = os.path.join(templates['tasks_path'], task)
            
            for level in completeness_levels:
                task_template_path = os.path.join(task_dir, f"{level}.json")
                task_json = load_json_file(task_template_path)
                
                prompt = assemble_prompt(lang_json, task_json)
                
                for model, endpoint in models.items():
                    generation_time = datetime.utcnow().isoformat()
                    try:
                        code = api_call(prompt, endpoint, model_name=model)
                        
                        file_extension = {
                            'python': 'py',
                            'javascript': 'js',
                            'go': 'go'
                        }.get(language)
                        
                        if not file_extension:
                            raise ValueError(f"Unsupported language: {language}")
                            
                        output_path = os.path.join(
                            base_output_dir,
                            language.lower(),
                            model.lower(),
                            level,
                            task,
                            f'Solution.{file_extension}'
                        )
                        save_Solution(code, output_path)
                        print(f"Generated code for {task}/{language.lower()}/{model.lower()}/{level}")
                        
                        # Record successful generation
                        task_metadata[task].append({
                            "task_id": f"{language.lower()}_{model.lower()}_{level}_{task}",
                            "task_name": task,
                            "prompt_type": level,
                            "language": language.lower(),
                            "model": model.lower(),
                            "generation_status": "success",
                            "generation_time": generation_time,
                            "generation_error": None
                        })
                        
                    except Exception as e:
                        # Record failed generation
                        task_metadata[task].append({
                            "task_id": f"{language.lower()}_{model.lower()}_{level}_{task}",
                            "task_name": task,
                            "prompt_type": level,
                            "language": language.lower(),
                            "model": model.lower(),
                            "generation_status": "error",
                            "generation_time": generation_time,
                            "generation_error": str(e)
                        })
                        print(f"Error generating code for {task}/{language.lower()}/{model.lower()}/{level}: {e}")
    
    for task, metadata_list in task_metadata.items():
        save_generation_metadata(task, metadata_list)


if __name__ == '__main__':
    generate_code()
