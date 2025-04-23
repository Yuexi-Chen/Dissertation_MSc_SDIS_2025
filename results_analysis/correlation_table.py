import pandas as pd
import numpy as np

tasks_df = pd.read_csv('table_output/task_metrics.csv')
langs_df = pd.read_csv('table_output/language_metrics.csv')
prompts_df = pd.read_csv('table_output/prompt_type_metrics.csv')

metrics = ['FC', 'HR', 'R', 'M', 'RB', 'S']

def calculate_correlation(data, metric, order):
    """
    Calculate the correlation between a metric and an ordered variable
    data: DataFrame containing metric data
    metric: Name of the metric to analyze
    order: List representing the order
    """
    return np.corrcoef(order, data[metric])[0,1]

# 1. Task Complexity Correlation
# Task complexity order: 1->2->3->4
task_order = [1, 2, 3, 4]  
task_correlations = {}
for metric in metrics:
    sorted_tasks = tasks_df.sort_values('task_name')
    task_correlations[metric] = round(calculate_correlation(sorted_tasks, metric, task_order), 2)

# 2. Language Impact Correlation
lang_correlations = {}
for metric in metrics:
    # Calculate the deviation of each language from the average performance for this metric
    mean_performance = langs_df[metric].mean()
    deviations = langs_df[metric] - mean_performance
    lang_correlations[metric] = deviations.std() / mean_performance

# 3. Prompt Completeness Correlation
# Prompt completeness order: minimal->partial->complete
prompt_order = [1, 2, 3]  # Increasing completeness
prompt_correlations = {}
for metric in metrics:
    prompt_correlations[metric] = round(calculate_correlation(prompts_df, metric, prompt_order), 2)

# Normalize language impact coefficients to the [-1, 1] range
max_lang_impact = max(abs(min(lang_correlations.values())), abs(max(lang_correlations.values())))
lang_correlations = {k: round(v/max_lang_impact, 2) for k, v in lang_correlations.items()}


results = pd.DataFrame({
    'Metric': metrics,
    'Task Complexity': [task_correlations[m] for m in metrics],
    'Language Impact': [lang_correlations[m] for m in metrics],
    'Prompt Completeness': [prompt_correlations[m] for m in metrics]
})

results.to_csv('table_output/correlation_heatmap.csv', index=False, float_format='%.2f')
print(results)