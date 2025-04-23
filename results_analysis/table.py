import pandas as pd
import numpy as np
import os
import argparse
from metrics import (load_ndjson, filter_valid_tasks, calculate_functional_correctness, 
                    calculate_readability, calculate_robustness, calculate_maintainability,
                    calculate_security, calculate_hallucination_rate)


def load_and_process_data(data_path, filters=None):
    """
    Load and process data, calculate metrics.

    Args:
        data_path: Path to the data file.
        filters: Dictionary of filter conditions {column_name: list of values}.

    Returns:
        The processed DataFrame.
    """
    print(f"Loading data from: {data_path}")
    df = load_ndjson(data_path)
    df = filter_valid_tasks(df)
    
    # Apply filters
    if filters:
        for column, values in filters.items():
            if column in df.columns and values:
                df = df[df[column].isin(values)]
    
    print(f"Filtered data contains {len(df)} records")
    if len(df) == 0:
        return None
    
    for col in ['model', 'language', 'prompt_type', 'task_name']:
        if col in df.columns:
            print(f"{col.capitalize()}: {df[col].unique()}")
    
    # Calculate various metrics
    print("Calculating metrics...")
    
    metrics_dfs = {}
    
    metrics_dfs['fc'] = calculate_functional_correctness(df)
    
    metrics_dfs['r'] = calculate_readability(df)
    
    try:
        metrics_dfs['rb'] = calculate_robustness(df)
        # Note: robustness metric is correctly named 'robustness' in the calculate_robustness function
        print("Successfully calculated robustness metric")
    except Exception as e:
        print(f"Warning: Could not calculate robustness - {e}")
        metrics_dfs['rb'] = None
    
    try:
        metrics_dfs['m'] = calculate_maintainability(df, metrics_dfs['r'])
    except Exception as e:
        print(f"Warning: Could not calculate maintainability - {e}")
        metrics_dfs['m'] = None
    
    try:
        metrics_dfs['s'] = calculate_security(df)
    except Exception as e:
        print(f"Warning: Could not calculate security - {e}")
        metrics_dfs['s'] = None
    
    try:
        metrics_dfs['hr'] = calculate_hallucination_rate(df)
    except Exception as e:
        print(f"Warning: Could not calculate hallucination rate - {e}")
        metrics_dfs['hr'] = None
    
    # Merge all available metrics
    result = metrics_dfs['fc'].copy()  
    
    print(f"FC DataFrame columns: {metrics_dfs['fc'].columns.tolist()}")
    print(f"Base result DataFrame columns before merging: {result.columns.tolist()}")
    
    # Check the data structure of each metric
    for name, metric_df in metrics_dfs.items():
        if metric_df is not None:
            print(f"Metric '{name}' DataFrame columns: {metric_df.columns.tolist()}")
            print(f"First row sample of '{name}': {metric_df.iloc[0].to_dict() if len(metric_df) > 0 else 'Empty'}")
    
    
    for name, metric_df in metrics_dfs.items():
        if name != 'fc' and metric_df is not None:  
            if 'task_id' in metric_df.columns and 'task_id' in result.columns:
                # Map metric names
                key_metric_map = {
                    'r': 'readability',
                    'rb': 'robustness',
                    'm': 'maintainability',
                    's': 'security',
                    'hr': 'hallucination_rate'
                }
                
                # Get the actual column name for this metric
                key_metric = key_metric_map.get(name, name)
                
                # Merge only if the column exists in metric_df
                if key_metric in metric_df.columns:
                    print(f"Merging '{key_metric}' from '{name}' DataFrame")
                    temp_df = metric_df[['task_id', key_metric]].copy()
                    temp_df = temp_df.drop_duplicates('task_id')
                    result = result.merge(temp_df, on='task_id', how='left')
                    print(f"After merging '{key_metric}', result columns: {result.columns.tolist()}")
                    if key_metric in result.columns:
                        print(f"First few values of '{key_metric}': {result[key_metric].head().tolist()}")
                else:
                    print(f"Warning: Column '{key_metric}' not found in DataFrame for '{name}'")
                    print(f"Available columns in '{name}': {metric_df.columns.tolist()}")
            else:
                missing_cols = []
                if 'task_id' not in metric_df.columns:
                    missing_cols.append(f"'task_id' in '{name}' DataFrame")
                if 'task_id' not in result.columns:
                    missing_cols.append("'task_id' in 'result' DataFrame")
                print(f"Warning: Cannot merge '{name}' because {' and '.join(missing_cols)} are missing")
    
    # Calculate CQS
    print("\nCalculating CQS (Composite Quality Score)...")
    
    required_metrics = ['functional_correctness', 'readability']
    optional_metrics = ['robustness', 'maintainability', 'security', 'hallucination_rate']
    
    missing_required = [m for m in required_metrics if m not in result.columns]
    missing_optional = [m for m in optional_metrics if m not in result.columns]
    
    if missing_required:
        print(f"Warning: Missing required metrics for full CQS calculation: {missing_required}")
        print("Will use simplified CQS calculation")
    
    if missing_optional:
        print(f"Note: Missing optional metrics: {missing_optional}")
    
    # Calculate CQS
    if not missing_required:  # All required metrics are available
        print("Using complete CQS formula")
        
        result['cqs'] = 0.3 * result['functional_correctness']
        print(f"CQS base (FC*0.3): Min={result['cqs'].min():.2f}, Max={result['cqs'].max():.2f}, Mean={result['cqs'].mean():.2f}")
        
        if 'readability' in result.columns:
            result['cqs'] += 0.2 * result['readability']
            print(f"After adding readability: Min={result['cqs'].min():.2f}, Max={result['cqs'].max():.2f}, Mean={result['cqs'].mean():.2f}")
        
        if 'robustness' in result.columns:
            result['cqs'] += 0.2 * result['robustness']
            print(f"After adding robustness: Min={result['cqs'].min():.2f}, Max={result['cqs'].max():.2f}, Mean={result['cqs'].mean():.2f}")
        
        if 'maintainability' in result.columns:
            result['cqs'] += 0.15 * result['maintainability']
            print(f"After adding maintainability: Min={result['cqs'].min():.2f}, Max={result['cqs'].max():.2f}, Mean={result['cqs'].mean():.2f}")
        
        if 'security' in result.columns:
            result['cqs'] += 0.1 * result['security']
            print(f"After adding security: Min={result['cqs'].min():.2f}, Max={result['cqs'].max():.2f}, Mean={result['cqs'].mean():.2f}")
        
        if 'hallucination_rate' in result.columns:
            # Hallucination rate is better when lower, so subtract from 100
            result['cqs'] += 0.05 * (100 - result['hallucination_rate']*100)
            print(f"After adding hallucination rate: Min={result['cqs'].min():.2f}, Max={result['cqs'].max():.2f}, Mean={result['cqs'].mean():.2f}")
    else:
        if 'readability' in result.columns:
            print("Using simplified CQS formula: 0.7*FC + 0.3*R")
            result['cqs'] = 0.7 * result['functional_correctness'] + 0.3 * result['readability']
        else:
            print("Using only functional_correctness as CQS")
            result['cqs'] = result['functional_correctness']  # Only functional correctness available
    
    print(f"Final CQS: Min={result['cqs'].min():.2f}, Max={result['cqs'].max():.2f}, Mean={result['cqs'].mean():.2f}")
    
    return result


def create_pivot_table(df, index_cols, columns_col, values_col, agg_func='mean', 
                       add_rank=True, sort_by_rank=True, output_path=None, column_order=None):
    """
    Create a pivot table and generate a CSV file.

    Args:
        df: Input data.
        index_cols: Column name(s) for row dimensions (can be a single string or a list).
        columns_col: Column name for column dimensions.
        values_col: Column name for values (cell content).
        agg_func: Aggregation function ('mean', 'median', 'sum', 'count', 'min', 'max').
        add_rank: Whether to add a rank column.
        sort_by_rank: Whether to sort by rank.
        output_path: Output file path.
        column_order: Sort order for columns.

    Returns:
        The generated pivot table DataFrame.
    """
    if isinstance(index_cols, str):
        index_cols = [index_cols]
    
    metrics_cols = ['functional_correctness', 'readability', 'robustness', 
                   'maintainability', 'security', 'hallucination_rate', 'cqs']
    
    # Special handling if metrics are used as columns or rows
    if columns_col == 'metrics':
        print("Using metrics as columns...")
        available_metrics = [col for col in metrics_cols if col in df.columns]
        print(f"Available metrics in data: {available_metrics}")
        
        print("\nSample data before melting:")
        print(df[available_metrics].head())
        
        selected_cols = index_cols + available_metrics
        selected_df = df[selected_cols].copy()
        
        melted_df = pd.melt(
            selected_df, 
            id_vars=index_cols,
            value_vars=available_metrics,
            var_name='metric',
            value_name='value'
        )
        
        print("\nSample melted data:")
        print(melted_df.head(10))
        
        pivot = pd.pivot_table(
            melted_df,
            values='value',
            index=index_cols,
            columns='metric',
            aggfunc=agg_func
        )
        
        print("\nPivot table before renaming columns:")
        print(pivot.head())
        
        # Rename columns to more user-friendly names
        column_mapping = {
            'functional_correctness': 'FC',
            'readability': 'R',
            'robustness': 'RB',
            'maintainability': 'M',
            'security': 'S',
            'hallucination_rate': 'HR',
            'cqs': 'CQS'
        }
        existing_cols = {col: column_mapping.get(col, col) for col in pivot.columns if col in column_mapping}
        if existing_cols:
            pivot = pivot.rename(columns=existing_cols)
            print(f"Renamed columns: {existing_cols}")
        
        print("\nPivot table after renaming columns:")
        print(pivot.head())
        
        if column_order:
            # Map the specified columns to friendly names
            mapped_column_order = [column_mapping.get(col, col) for col in column_order if column_mapping.get(col, col) in pivot.columns]
            if mapped_column_order:
                other_cols = [col for col in pivot.columns if col not in mapped_column_order]
                pivot = pivot[mapped_column_order + other_cols]
    
    elif 'metrics' in index_cols:
        print("Using metrics as rows...")
        idx_pos = index_cols.index('metrics')
        other_idx = [idx for i, idx in enumerate(index_cols) if i != idx_pos]
        
        dimension_cols = other_idx + [columns_col]
        available_metrics = [col for col in metrics_cols if col in df.columns]
        print(f"Available metrics in data: {available_metrics}")
        selected_df = df[dimension_cols + available_metrics].copy()
        
        melted_df = pd.melt(
            selected_df,
            id_vars=dimension_cols,
            value_vars=available_metrics,
            var_name='metric',
            value_name=values_col
        )
        
        # Map metric names to friendly names
        metric_mapping = {
            'functional_correctness': 'FC',
            'readability': 'R',
            'robustness': 'RB',
            'maintainability': 'M',
            'security': 'S',
            'hallucination_rate': 'HR',
            'cqs': 'CQS'
        }
        print(f"Using metric mapping: {metric_mapping}")
        
        melted_df['metric'] = melted_df['metric'].apply(lambda x: metric_mapping.get(x, x))
        
        new_index_cols = [col if col != 'metrics' else 'metric' for col in index_cols]
        
        pivot = pd.pivot_table(
            melted_df,
            values=values_col,
            index=new_index_cols,
            columns=columns_col,
            aggfunc=agg_func
        )
        
        if column_order:
            valid_cols = [col for col in column_order if col in pivot.columns]
            if valid_cols:
                other_cols = [col for col in pivot.columns if col not in valid_cols]
                pivot = pivot[valid_cols + other_cols]
    
    else:
        # Original pivot table logic
        print(f"Creating pivot table with rows: {index_cols}, columns: {columns_col}, values: {values_col}")
        pivot = pd.pivot_table(
            df, 
            values=values_col,
            index=index_cols,
            columns=columns_col,
            aggfunc=agg_func
        )
        
        if column_order:
            valid_cols = [col for col in column_order if col in pivot.columns]
            if len(valid_cols) != len(column_order):
                missing_cols = set(column_order) - set(valid_cols)
                print(f"Warning: Some columns were not found: {missing_cols}")
            
            other_cols = [col for col in pivot.columns if col not in column_order]
            
            # Reorder
            if valid_cols:
                pivot = pivot[valid_cols + other_cols]
                print(f"Columns reordered to: {valid_cols + other_cols}")
    
    # Average column
    if pivot.shape[1] > 1:  # If there are multiple columns
        pivot['Average'] = pivot.mean(axis=1)
    
    # Rank column and sort
    if add_rank and 'Average' in pivot.columns:
        # Use different sort directions for different metrics
        ascending = True if values_col == 'hallucination_rate' else False
        pivot['Rank'] = pivot['Average'].rank(ascending=ascending)
        
        if sort_by_rank:
            pivot = pivot.sort_values('Rank')
    
    # Round to 2 decimal places
    pivot = pivot.round(2)
    
    if output_path:
        print(f"Saving to {output_path}")
        pivot.to_csv(output_path)
    
    return pivot


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Generate flexible tables from evaluation data')
    
    # Basic parameters
    parser.add_argument('--data_path', type=str, default='merged_results.ndjson',
                      help='Path to the merged results data file')
    parser.add_argument('--output_dir', type=str, default='table_output',
                      help='Directory to save output files')
    parser.add_argument('--output_file', type=str, default='results_table.csv',
                      help='Output CSV filename')
    
    # Filter parameters
    parser.add_argument('--models', type=str, nargs='+', default=None,
                      help='Filter by specific models')
    parser.add_argument('--languages', type=str, nargs='+', default=None,
                      help='Filter by specific languages')
    parser.add_argument('--prompt_types', type=str, nargs='+', default=None,
                      help='Filter by specific prompt types')
    parser.add_argument('--tasks', type=str, nargs='+', default=None,
                      help='Filter by specific task names')
    
    # Table structure parameters
    parser.add_argument('--index', type=str, nargs='+', default=['model'],
                      help='Column(s) to use as index (rows). Use "metrics" to use metrics as rows.')
    parser.add_argument('--columns', type=str, default='language',
                      help='Column to use for pivot table columns. Use "metrics" to use metrics as columns.')
    parser.add_argument('--values', type=str, default='cqs',
                      help='Value to display in cells (functional_correctness, readability, robustness, maintainability, security, hallucination_rate, cqs)')
    parser.add_argument('--agg_func', type=str, default='mean',
                      help='Aggregation function (mean, median, sum, count, min, max)')
    parser.add_argument('--column_order', type=str, nargs='+', default=None,
                      help='Custom order for columns (e.g., "complete partial minimal" or "functional_correctness readability")')
    
    # Table options
    parser.add_argument('--no_rank', action='store_true',
                      help='Do not add rank column')
    parser.add_argument('--no_sort', action='store_true',
                      help='Do not sort by rank')
    
    return parser.parse_args()


def main():
    args = parse_arguments()
    
    os.makedirs(args.output_dir, exist_ok=True)
    output_path = os.path.join(args.output_dir, args.output_file)
    
    filters = {}
    if args.models is not None:
        filters['model'] = args.models
    if args.languages is not None:
        filters['language'] = args.languages
    if args.prompt_types is not None:
        filters['prompt_type'] = args.prompt_types
    if args.tasks is not None:
        filters['task_name'] = args.tasks
    
    result_df = load_and_process_data(args.data_path, filters)
    
    if result_df is None or len(result_df) == 0:
        print("No data available after filtering. Check the filter criteria.")
        return
    
    if args.columns != 'metrics' and 'metrics' not in args.index:
        value_mapping = {
            'fc': 'functional_correctness',
            'r': 'readability',
            'rb': 'robustness',
            'm': 'maintainability',
            's': 'security',
            'hr': 'hallucination_rate'
        }
        
        requested_value = value_mapping.get(args.values, args.values)
        print(f"Looking for value: {requested_value} (original input: {args.values})")
        
        if requested_value not in result_df.columns:
            print(f"Warning: Requested value '{requested_value}' not found in data.")
            print(f"Available values: {', '.join(result_df.columns)}")
            print("Using 'functional_correctness' as fallback.")
            args.values = 'functional_correctness'
        else:
            args.values = requested_value
    
    pivot = create_pivot_table(
        result_df,
        index_cols=args.index,
        columns_col=args.columns,
        values_col=args.values,
        agg_func=args.agg_func,
        add_rank=not args.no_rank,
        sort_by_rank=not args.no_sort,
        output_path=output_path,
        column_order=args.column_order
    )
    
    print("\nGenerated Table:")
    print("=" * 50)
    print(pivot)
    print("=" * 50)
    print(f"Table saved to: {output_path}")


if __name__ == "__main__":
    main() 