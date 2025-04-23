import os
import pandas as pd


# Constants
RESULTS_DIR = "../results"
OUTPUT_DIR = "."
SUBDIRS = ["generation", "execution", "test_results", "static_analysis", "hallucination"]

def merge_task_files(subdir_name):
    """
    Merge all task.ndjson files in a subdirectory into a single file
    """
    print(f"Merging files in {subdir_name}...")
    subdir_path = os.path.join(RESULTS_DIR, subdir_name)
    output_file = os.path.join(OUTPUT_DIR, f"{subdir_name}.ndjson")
    
    dfs = []
    for task_file in os.listdir(subdir_path):
        if task_file.startswith("task_") and task_file.endswith(".ndjson"):
            file_path = os.path.join(subdir_path, task_file)
            try:
                df = pd.read_json(file_path, lines=True)
                dfs.append(df)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    # Combine all DataFrames
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        combined_df.to_json(output_file, orient='records', lines=True)
        print(f"Created {output_file} with {len(combined_df)} records")
        return combined_df
    else:
        print(f"No valid files found in {subdir_path}")
        return pd.DataFrame()

def merge_all_files():
    """
    Merge the consolidated files from each subdirectory into a single file
    using task_id as the key. Excludes test_results data due to its different structure.
    """
    print("Merging all consolidated files (excluding test_results)...")
    merged_data = {}
    
    merge_subdirs = [s for s in SUBDIRS if s != "test_results"]
    
    dataframes = {}
    for subdir in merge_subdirs:
        file_path = os.path.join(OUTPUT_DIR, f"{subdir}.ndjson")
        if os.path.exists(file_path):
            try:
                df = pd.read_json(file_path, lines=True)
                dataframes[subdir] = df
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    if "generation" in dataframes:
        base_df = dataframes["generation"]
        
        for _, row in base_df.iterrows():
            task_id = row["task_id"]
            merged_data[task_id] = {"task_id": task_id}
            merged_data[task_id]["status"] = "valid"
            
            for col in base_df.columns:
                if col == "task_id":
                    merged_data[task_id][col] = row[col]
                elif col != "timestamp" and not col.endswith("_timestamp") and col != "generation_time":
                    merged_data[task_id][col] = row[col]
        
        for subdir, df in dataframes.items():
            if subdir == "generation":
                continue  
                
            for task_id in merged_data.keys():
                matching_rows = df[df["task_id"] == task_id]
                
                if len(matching_rows) > 0:
                    for col in df.columns:
                        if col == "task_id":
                            continue  
                        
                        if col == "timestamp" or col.endswith("_timestamp") or "time" in col.lower():
                            continue 
                        elif col in merged_data[task_id] and col not in ["task_name", "language", "model", "prompt_type"]:
                            field_name = f"{subdir}_{col}"
                            merged_data[task_id][field_name] = matching_rows.iloc[0][col]
                        else:
                            merged_data[task_id][col] = matching_rows.iloc[0][col]
                else:
                    if merged_data[task_id]["status"] != "invalid":
                        merged_data[task_id]["status"] = "invalid"
    
    final_df = pd.DataFrame(list(merged_data.values()))
    
    output_file = os.path.join(OUTPUT_DIR, "merged_results.ndjson")
    final_df.to_json(output_file, orient='records', lines=True)
    print(f"Created {output_file} with {len(final_df)} records")
    return final_df

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for subdir in SUBDIRS:
        merge_task_files(subdir)
    
    merge_all_files()

if __name__ == "__main__":
    main() 