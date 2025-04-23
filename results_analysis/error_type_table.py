import json
import pandas as pd
from collections import Counter, defaultdict
from pathlib import Path

def load_data(file_path: Path) -> list[dict]:
    data = []
    with file_path.open('r', encoding='utf-8') as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON line: {line.strip()}")
    return data

def analyze_error_types(data: list[dict]) -> pd.DataFrame:
    """Analyzes the distribution of error types per language."""
    error_counts = defaultdict(Counter)
    for record in data:
        language = record.get('language')
        error_type = record.get('error_type')
        if language and error_type:
            error_counts[language][error_type] += 1

    df = pd.DataFrame.from_dict(error_counts, orient='index')
    df = df.fillna(0).astype(int) 
    all_languages = set(record.get('language') for record in data if record.get('language'))
    df = df.reindex(list(all_languages), fill_value=0)
    df.index.name = 'language'
    df = df.sort_index() 
    df = df.sort_index(axis=1) 
    return df

def analyze_error_types_by_task(data: list[dict]) -> pd.DataFrame:
    """Analyzes the distribution of error types per task."""
    error_counts = defaultdict(Counter)
    for record in data:
        task_name = record.get('task_name')
        error_type = record.get('error_type')
        if task_name and error_type:
            error_counts[task_name][error_type] += 1

    df = pd.DataFrame.from_dict(error_counts, orient='index')
    df = df.fillna(0).astype(int) 
    all_tasks = sorted(list(set(record.get('task_name') for record in data if record.get('task_name'))))
    df = df.reindex(all_tasks, fill_value=0)
    df.index.name = 'task_name'
    df = df.sort_index() 
    df = df.sort_index(axis=1) 
    return df

def save_to_csv(dataframe: pd.DataFrame, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_path)
    print(f"Analysis results saved to: {output_path}")

def main():
    script_dir = Path(__file__).parent
    data_file = script_dir / 'merged_results.ndjson'
    language_output_file = script_dir / 'table_output/language_error_type.csv'
    task_output_file = script_dir / 'table_output/task_error_type.csv'

    print(f"Loading data from: {data_file}")
    data = load_data(data_file)

    # Language Error Type
    print("\nAnalyzing error types by language...")
    language_error_distribution = analyze_error_types(data)
    print(f"Saving language error type results to: {language_output_file}")
    save_to_csv(language_error_distribution, language_output_file)

    # Task Error Type
    print("\nAnalyzing error types by task...")
    task_error_distribution = analyze_error_types_by_task(data)
    print(f"Saving task error type results to: {task_output_file}")
    save_to_csv(task_error_distribution, task_output_file)

    print("\nAnalysis complete.")

if __name__ == "__main__":
    main() 