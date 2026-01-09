# Read an input path and aggregate CSV files found there into a single output CSV file.
from datetime import datetime, timedelta
import os
import pandas as pd
import sys
from typing import List

import pytz

# Store in an array all the HTTP error codes which can be produced
HTTP_ERROR_CODES = [404, 423, 500, 503, 508]

def parse_timestamp(ts: str) -> datetime:
    if sys.version_info >= (3, 11):
        return datetime.fromisoformat(ts)

    ts = ts.rstrip('Z')

    if '.' in ts:
        main, frac = ts.split('.')
        # Normalize fractional seconds to microseconds
        frac = (frac + "000000")[:6]
        ts = f"{main}.{frac}"
        fmt = '%Y-%m-%dT%H:%M:%S.%f'
    else:
        fmt = '%Y-%m-%dT%H:%M:%S'

    return datetime.strptime(ts, fmt).replace(tzinfo=pytz.utc)

# Modify function signature to match the new requirements
def aggregate_csv_files(input_path: str, output_file: str, seed: int = 0, time_interval: int = 15, columns: List[str] = None) -> None:
    """
    Aggregates all CSV files in the given input path into a single CSV file.

    Parameters:
    - input_path: str - The directory containing CSV files to aggregate.
    - output_file: str - The path to the output CSV file.
    - columns: List[str] - Optional list of columns to include in the output. If None, all columns are included.
    """
    all_files = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.endswith('.csv') and f.startswith("results_log_")]
    
    if not all_files:
        print("No CSV files found in the specified directory.")
        return

    df_list = []
    for file in all_files:
        df = pd.read_csv(file)
        if columns:
            df = df[columns]

        df_list.append(df)

    # Once I have all the dataframes, I need to aggregate them using the StartTime information.
    # I know what is the maximum and the minimum, so I will decide a fixed time interval.
    # For each subdivision, I will calculate the average latency, median latency, variance, number of total requests, number of correct requests, number of failed requests.
    # Then I will write all these information into a new CSV file, named as "rounds_<output_file>".
    # This file contains also the total number of clients, total number of collections (passed in the arguments), and seed of the experiment (again passed in the arguments).
    df = pd.concat(df_list, ignore_index=True)

    # Add synthetic columns for StatusCode if not present
    if 'StatusCode' not in df.columns:
        df['StatusCode'] = 200

    # Convert StartTime to datetime
    df['StartTime'] = df['StartTime'].apply(parse_timestamp)
    df = df.sort_values(by='StartTime')
    min_time = df['StartTime'].min()
    max_time = df['StartTime'].max()
    total_duration = (max_time - min_time).total_seconds()
    # Calculate number of subdivisions based on time_interval
    subdivisions = int(total_duration // time_interval) + 1
    # Split the dataframe into subdivisions based on StartTime
    for i in range(subdivisions):
        start_interval = min_time + timedelta(seconds=i * time_interval)
        end_interval = min_time + timedelta(seconds=(i + 1) * time_interval)
        sub_df = df[(df['StartTime'] >= start_interval) & (df['StartTime'] < end_interval)]
        # Calculate metrics for this subdivision
        if not sub_df.empty:
            avg_latency = sub_df['FuncDuration'].mean()
            median_latency = sub_df['FuncDuration'].median()
            variance_latency = sub_df['FuncDuration'].var()
            total_requests = len(sub_df)
            correct_requests = len(sub_df[sub_df['StatusCode'] == 200])
            failed_requests = total_requests - correct_requests
            # Calculate also the quartiles of the latency distribution
            Q1 = sub_df['FuncDuration'].quantile(0.25)
            Q2 = sub_df['FuncDuration'].quantile(0.5)
            Q3 = sub_df['FuncDuration'].quantile(0.75)
            Q4 = sub_df['FuncDuration'].quantile(1.0)

            metrics = {
                'Seed': seed,
                'Round': i + 1,
                'StartInterval': start_interval,
                'EndInterval': end_interval,
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
            # Write to the output file called "rounds_<output_file> "
            rounds_output_file = f"rounds_{os.path.basename(output_file)}"
            write_header = not os.path.exists(rounds_output_file)
            with open(rounds_output_file, 'a') as f:
                metrics_df.to_csv(f, header=write_header, index=False)
            
            print(f"Processed round {i + 1}/{subdivisions}...")    
    print(f"Aggregated rounds into {rounds_output_file}.")

    # CALCULATE FOR THE WHOLE EXPERIMENT: average latency, median latency, variance, number of total requests, number of correct requests, number of failed requests
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
    # Also create one column for each HTTP error code, plus one for other errors
    error_code_counts = {code: len(df[df['StatusCode'] == code]) for code in HTTP_ERROR_CODES}
    other_errors = len(df[(df['StatusCode'] != 200) & (~df['StatusCode'].isin(HTTP_ERROR_CODES))])

    metrics = {
        'Seed': seed,
        'AverageLatency': avg_latency,
        'MedianLatency': median_latency,
        'VarianceLatency': variance_latency,
        'Q1': Q1,
        'Q2': Q2,
        'Q3': Q3,
        'Q4': Q4,
        'TotalRequests': total_requests,
        'CorrectRequests': correct_requests,
        'FailedRequests': failed_requests,
        **error_code_counts,
        'OtherErrors': other_errors
    }
    metrics_df = pd.DataFrame([metrics])

    # Check if output file exists to decide whether to write header or not
    write_header = not os.path.exists(output_file)
    with open(output_file, 'a') as f:
        metrics_df.to_csv(f, header=write_header, index=False)

    print(f"Aggregated {len(all_files)} files into {output_file}.")

if __name__ == "__main__":
    # Take the input path, output file, number of subdivisions, number of clients, number of collections, and seed from command line arguments
    in_dir = sys.argv[1] if len(sys.argv) > 1 else "ermes_benchmark/micro_bench/results/csv_results/"
    out_file = sys.argv[2] if len(sys.argv) > 2 else "ermes_benchmark/micro_bench/results/aggregated_results.csv"
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    time_interval = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    # Call the aggregation function
    aggregate_csv_files(in_dir, out_file, seed, time_interval)