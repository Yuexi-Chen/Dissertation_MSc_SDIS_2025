import pandas as pd
import json


def load_ndjson(filepath):
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    return pd.DataFrame(data)


def filter_valid_tasks(df):
    return df[df['status'] == 'valid']


def calculate_eqs(row):
    if row['execution_status'] == 'success':
        return 1.0
    
    # calculate based on error type
    error_weights = {
        'SyntaxError': 1.0,
        'RuntimeError': 0.7,
        'ImportError': 0.7,
        'NameError': 0.7,
        'TypeError': 0.7,
        'ValueError': 0.4,
        'KeyError': 0.4,
        'IndexError': 0.4,
        'AttributeError': 0.7
    }
    
    error_type = row['error_type']
    if error_type in error_weights:
        return 1 - error_weights[error_type]
    elif error_type:
        return 0.3  
    return 1.0


def calculate_functional_correctness(df):
    """
    Calculate Functional Correctness (FC) metric
    FC = (0.3 × EQS + 0.7 × TPR) × 100
    
    Args:
        df: DataFrame with merged results
        
    Returns:
        DataFrame with FC scores
    """
    # Apply EQS calculation
    df_result = df.copy()
    df_result['eqs'] = df_result.apply(calculate_eqs, axis=1)
    
    # Calculate Test Pass Rate (TPR)
    df_result['tpr'] = df_result['test_passed_count'] / df_result['test_total_count']
    df_result['tpr'] = df_result['tpr'].fillna(0) 
    
    # Calculate Functional Correctness
    df_result['functional_correctness'] = (0.3 * df_result['eqs'] + 0.7 * df_result['tpr']) * 100
    
    return df_result[['task_id', 'model', 'language', 'prompt_type', 'task_name', 
                   'eqs', 'tpr', 'functional_correctness']]


def extract_code_smells(row):
    if isinstance(row['code_smells'], (int, float)):
        return row['code_smells']
    elif isinstance(row['issues'], dict) and 'total' in row['issues']:
        return row['issues']['total']
    return 0


def calculate_readability(df):
    """
    Calculate Readability (R) metric
    R = 100 - (0.3×CC + 0.3×COG + 0.2×(1-CR) + 0.15×DUP + 0.05×CS)×100
    
    Args:
        df: DataFrame with merged results
        
    Returns:
        DataFrame with Readability scores
    """
    df_result = df.copy()
    
    # Use the 95th percentile of the dataset as the normalization threshold, following a data-driven approach
    max_cc = df_result['cyclomatic_complexity'].quantile(0.95)
    max_cog = df_result['cognitive_complexity'].quantile(0.95)
    
    # Ensure a reasonable minimum threshold
    max_cc = max(10, max_cc)  # Ensure minimum value is 10
    max_cog = max(15, max_cog)  # Ensure minimum value is 15
    
    # Calculate the upper limit for average code smells per 1000 lines of code
    # Typically, no more than 5 code smells per 1000 lines of code are recommended
    avg_loc = df_result['lines_of_code'].mean() if 'lines_of_code' in df_result.columns else 1000
    max_cs = max(5, 5 * (avg_loc / 1000))  
    
    # Normalize metrics
    df_result['norm_cc'] = df_result['cyclomatic_complexity'] / max_cc
    df_result['norm_cog'] = df_result['cognitive_complexity'] / max_cog
    df_result['norm_cr'] = df_result['comment_coverage'] / 100  
    df_result['norm_dup'] = df_result['code_redundancy'] / 100  
    
    # Handle code smells
    df_result['extracted_smells'] = df_result.apply(extract_code_smells, axis=1)
    df_result['norm_cs'] = df_result['extracted_smells'] / max_cs
    
    # Limit all normalized values to the 0-1 range
    for col in ['norm_cc', 'norm_cog', 'norm_cr', 'norm_dup', 'norm_cs']:
        df_result[col] = df_result[col].clip(0, 1)
    
    # Calculate readability
    df_result['readability'] = 100 - (0.3*df_result['norm_cc'] + 0.3*df_result['norm_cog'] + 
                               0.2*(1-df_result['norm_cr']) + 0.15*df_result['norm_dup'] + 
                               0.05*df_result['norm_cs']) * 100
    
    return df_result[['task_id', 'model', 'language', 'prompt_type', 'task_name',
                  'norm_cc', 'norm_cog', 'norm_cr', 'norm_dup', 'norm_cs', 'readability']]


def categorize_error(error_msg):
    """Categorize error messages into defined categories."""
    if not error_msg or error_msg == "":
        return None
        
    patterns = {
        'null_handling': ["undefined", "null pointer", "KeyError", "Cannot read properties of undefined", 
                         "NoneType", "TypeError: cannot read", "is not defined"],
        'type_validation': ["TypeError", "cannot use", "not supported between", "cannot convert",
                           "expected", "invalid type"],
        'input_validation': ["ValueError", "invalid input", "out of range", "invalid argument",
                            "IndexError"],
        'exception_handling': ["Exception", "Error:", "uncaught", "unexpected"]
    }
    
    for category, signatures in patterns.items():
        if any(signature.lower() in error_msg.lower() for signature in signatures):
            return category
    
    return "other"


def calculate_robustness(df):
    """
    Calculate Robustness (RB) metric based on error patterns
    RB = 100 - Σ(w_i × d_i)
    
    Args:
        df: DataFrame with merged results
        
    Returns:
        DataFrame with Robustness scores
    """
    df_result = df.copy()
    
    pattern_weights = {
        'null_handling': 30,
        'type_validation': 25,
        'input_validation': 30,
        'exception_handling': 15
    }
    
    df_result['error_category'] = df_result['error_message'].apply(categorize_error)
    
    results = []
    
    for (model, language, prompt_type, task_name), group in df_result.groupby(['model', 'language', 'prompt_type', 'task_name']):
        total_tasks = len(group)
        deficiencies = {cat: 0 for cat in pattern_weights}
        
        for cat, weight in pattern_weights.items():
            count = sum(group['error_category'] == cat)
            # Directly calculate the deficiency degree in the 0-1 range
            deficiencies[cat] = min(count / max(1, total_tasks), 1.0)
        
        robustness_score = 100 - sum(pattern_weights[cat] * deficiencies[cat] for cat in pattern_weights)
        robustness_score = max(0, robustness_score)
        
        # Get all task_ids in this group
        task_ids = group['task_id'].unique()
        
        # Create a record for each task_id
        for task_id in task_ids:
            results.append({
                'task_id': task_id,
                'model': model,
                'language': language,
                'prompt_type': prompt_type,
                'task_name': task_name,
                'robustness': robustness_score,
                **{f"{cat}_deficiency": deficiencies[cat] * 100 for cat in pattern_weights}  # Convert to percentage for display
            })
    
    return pd.DataFrame(results)


def calculate_maintainability(df, readability_df=None):
    """
    Calculate Maintainability (M) metric
    M = 0.7×SQ_MR + 0.3×CMS
    
    Args:
        df: DataFrame with merged results
        readability_df: Optional pre-calculated readability DataFrame
        
    Returns:
        DataFrame with Maintainability scores
    """
    df_result = df.copy()
        
    # Convert SonarQube maintainability rating (1-5) to a 0-100 score, maintaining the correct directionality
    # Rating is 1-5, where 1(A) is the best and 5(E) is the worst
    df_result['sq_mr'] = (6 - df_result['maintainability_rating']) * 20  # Convert to 0-100 score
    
    # Handle missing values
    df_result['sq_mr'] = df_result['sq_mr'].fillna(50)  
    
    # Calculate Custom Maintainability Score (CMS)
    # Get normalized metrics from readability if not provided
    if readability_df is None:
        readability_df = calculate_readability(df)
    
    # Merge readability metrics
    cms_df = df_result.merge(readability_df[['task_id', 'norm_cc', 'norm_cog', 'norm_cr', 'norm_dup']], 
                     on='task_id', how='left')
    
    # Use the 95th percentile of the dataset as the technical debt threshold
    max_td = df_result['technical_debt'].quantile(0.95)
    max_td = max(20, max_td)  
    
    cms_df['norm_td'] = cms_df['technical_debt'] / max_td
    cms_df['norm_td'] = cms_df['norm_td'].clip(0, 1)  
    
    # Calculate CMS
    cms_df['cms'] = 100 - (0.3*cms_df['norm_cc'] + 0.3*cms_df['norm_cog'] + 
                          0.15*(1-cms_df['norm_cr']) + 0.15*cms_df['norm_dup'] + 
                          0.1*cms_df['norm_td']) * 100
    
    cms_df['maintainability'] = 0.7 * cms_df['sq_mr'] + 0.3 * cms_df['cms']
    
    return cms_df[['task_id', 'model', 'language', 'prompt_type', 'task_name',
                  'sq_mr', 'cms', 'maintainability']]


def calculate_security(df):
    """
    Calculate Security (S) metric
    S = 100 - (0.4×V + 0.3×(1-SR) + 0.2×(1-RR) + 0.1×D)×100
    
    Args:
        df: DataFrame with merged results
        
    Returns:
        DataFrame with Security scores
    """
    df_result = df.copy()
        
    max_vulns = df_result['vulnerabilities'].quantile(0.95) if 'vulnerabilities' in df_result.columns else 5
    max_bugs = df_result['bugs'].quantile(0.95) if 'bugs' in df_result.columns else 5
    
    max_vulns = max(3, max_vulns)  
    max_bugs = max(3, max_bugs)  
    
    df_result['norm_vulns'] = df_result['vulnerabilities'] / max_vulns
    df_result['norm_bugs'] = df_result['bugs'] / max_bugs
    
    # invert then normalize ratings
    # Rating is 1-5, where 1(A) is the best and 5(E) is the worst
    df_result['norm_sr'] = (6 - df_result['security_rating']) / 5  # A->1.0, E->0.2
    df_result['norm_rr'] = (6 - df_result['reliability_rating']) / 5  # A->1.0, E->0.2
    
    # Limit all normalized values to the 0-1 range
    for col in ['norm_vulns', 'norm_bugs', 'norm_sr', 'norm_rr']:
        df_result[col] = df_result[col].fillna(0.5)  
        df_result[col] = df_result[col].clip(0, 1)
    
    # Calculate security score
    # Note: When using (1-norm_sr) and (1-norm_rr), high scores (A-level) receive a low penalty
    df_result['security'] = 100 - (0.4*df_result['norm_vulns'] + 0.3*(1-df_result['norm_sr']) + 
                               0.2*(1-df_result['norm_rr']) + 0.1*df_result['norm_bugs']) * 100
    
    return df_result[['task_id', 'model', 'language', 'prompt_type', 'task_name',
                  'norm_vulns', 'norm_sr', 'norm_rr', 'norm_bugs', 'security']]


def calculate_ehs(row):
    # Calculate Explicit Hallucination Score for a single row.
    hallucination_weights = {
        'nonexistent_library': 0.3,
        'undefined_function': 0.3,
        'invalid_api_usage': 0.25,
        'syntax_error': 0.15
    }
    
    if not isinstance(row['explicit_hallucinations'], dict):
        return 0
            
    total = 0
    for h_type, weight in hallucination_weights.items():
        if h_type in row['explicit_hallucinations'] and row['explicit_hallucinations'][h_type]:
            total += weight
    return total


def calculate_hallucination_rate(df):
    """
    Calculate Hallucination Rate (HR) metric
    HR = 0.6×EHS + 0.4×IHR
    
    Args:
        df: DataFrame with merged results
        
    Returns:
        DataFrame with Hallucination Rate scores
    """
    df_result = df.copy()
    
    df_result['ehs'] = df_result.apply(calculate_ehs, axis=1)
    
    # Calculate Implicit Hallucination Rate (IHR) using test failure rate
    df_result['ihr'] = 1 - df_result['test_passed_count'] / df_result['test_total_count']
    df_result['ihr'] = df_result['ihr'].fillna(0.5)  
    
    df_result['hallucination_rate'] = 0.6 * df_result['ehs'] + 0.4 * df_result['ihr']
    
    return df_result[['task_id', 'model', 'language', 'prompt_type', 'task_name',
                  'ehs', 'ihr', 'hallucination_rate']]


def calculate_comprehensive_quality_score(merged_results_path, test_results_path=None):
    """
    Calculate Comprehensive Quality Score (CQS) metric
    CQS = 0.3×FC + 0.2×R + 0.2×RB + 0.15×M + 0.1×S + 0.05×(100-HR×100)
    
    Args:
        merged_results_path: Path to the merged_results.ndjson file
        test_results_path: Path to the test_results.ndjson file (optional)
        
    Returns:
        DataFrame with CQS scores
    """
    df = load_ndjson(merged_results_path)
    df = filter_valid_tasks(df)
    
    fc_df = calculate_functional_correctness(df)
    r_df = calculate_readability(df)
    rb_df = calculate_robustness(df)
    m_df = calculate_maintainability(df, r_df)
    s_df = calculate_security(df)
    hr_df = calculate_hallucination_rate(df)
    
    metrics = [
        ('functional_correctness', fc_df, 0.3),
        ('readability', r_df, 0.2),
        ('robustness', rb_df, 0.2),
        ('maintainability', m_df, 0.15),
        ('security', s_df, 0.1)
    ]
    
    result = metrics[0][1][['task_id', 'model', 'language', 'prompt_type', 'task_name', 
                        metrics[0][0]]]
    
    for name, df, weight in metrics[1:]:
        result = result.merge(df[['task_id', name]], on='task_id', how='left')
    
    result = result.merge(hr_df[['task_id', 'hallucination_rate']], on='task_id', how='left')
    
    result['cqs'] = (0.3 * result['functional_correctness'] +
                    0.2 * result['readability'] +
                    0.2 * result['robustness'] +
                    0.15 * result['maintainability'] +
                    0.1 * result['security'] +
                    0.05 * (100 - result['hallucination_rate']*100))
    
    return result


def create_pivot_table(df, index_cols, values_col, columns_col='task_name', aggfunc='mean',
                     include_average=True, round_digits=1):
    """
    Create a pivot table with optional average row and column.
    
    Args:
        df: DataFrame with the metrics data
        index_cols: Column(s) to use as index
        values_col: Column to aggregate
        columns_col: Column to use as columns
        aggfunc: Aggregation function ('mean', 'sum', etc.)
        include_average: Whether to include average row/column
        round_digits: Number of digits to round to
        
    Returns:
        Pivot table as DataFrame
    """
    pivot = pd.pivot_table(df, values=values_col, index=index_cols, 
                          columns=columns_col, aggfunc=aggfunc)
    
    if isinstance(index_cols, str):
        pivot = pivot.sort_index()
    
    if include_average and len(pivot.columns) > 1:
        pivot['Average'] = pivot.mean(axis=1)
    
    if include_average and len(pivot.index) > 1:
        avg_row = pivot.mean()
        pivot.loc['Average'] = avg_row
    
    pivot = pivot.round(round_digits)
    
    return pivot 