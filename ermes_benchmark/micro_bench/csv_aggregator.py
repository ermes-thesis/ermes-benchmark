# Read an input path and aggregate CSV files found there into a single output CSV file.
import os
import pandas as pd
import sys
from typing import List

def aggregate_csv_files(input_path: str, output_file: str, columns: List[str] = None) -> None:
    """
    Aggregates all CSV files in the given input path into a single CSV file.

    Parameters:
    - input_path: str - The directory containing CSV files to aggregate.
    - output_file: str - The path to the output CSV file.
    - columns: List[str] - Optional list of columns to include in the output. If None, all columns are included.
    """
    all_files = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.endswith('.csv')]
    
    if not all_files:
        print("No CSV files found in the specified directory.")
        return

    df_list = []
    for file in all_files:
        df = pd.read_csv(file)
        if columns:
            df = df[columns]

        df_list.append(df)

    # CALCULATE FOR THE WHOLE EXPERIMENT: average latency, median latency, variance, number of total requests, number of correct requests, number of failed requests
    df = pd.concat(df_list, ignore_index=True)
    avg_latency = df['FuncDuration'].mean()
    median_latency = df['FuncDuration'].median()
    variance_latency = df['FuncDuration'].var()
    # Extract all the quartiles of the latency distribution
    Q1 = df['FuncDuration'].quantile(0.25)
    Q2 = df['FuncDuration'].quantile(0.5)
    Q3 = df['FuncDuration'].quantile(0.75)
    Q4 = df['FuncDuration'].quantile(1.0)

    # The failed requests contain a status code different from 200
    total_requests = len(df)
    correct_requests = len(df[df['StatusCode'] == 200])
    failed_requests = total_requests - correct_requests

    metrics = {
        'AverageLatency': avg_latency,
        'MedianLatency': median_latency,
        'VarianceLatency': variance_latency,
        'Q1': Q1,
        'Q2': Q2,
        'Q3': Q3,
        'Q4': Q4,
        'TotalRequests': total_requests,
        'CorrectRequests': correct_requests,
        'FailedRequests': failed_requests
    }
    metrics_df = pd.DataFrame([metrics])

    # Check if output file exists to decide whether to write header or not
    write_header = not os.path.exists(output_file)
    with open(output_file, 'a') as f:
        metrics_df.to_csv(f, header=write_header, index=False)

    print(f"Aggregated {len(all_files)} files into {output_file}.")

if __name__ == "__main__":
    # Take the input path and output file from arguments or set defaults for testing
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "ermes_benchmark/micro_bench/results/csv_results/"
    out_file = sys.argv[2] if len(sys.argv) > 2 else "ermes_benchmark/micro_bench/results/aggregated_results.csv"
    aggregate_csv_files(out_dir, out_file)