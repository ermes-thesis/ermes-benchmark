import os
import re
import sys
import zipfile
from datetime import datetime
from typing import Dict

import pandas as pd
import pytz

import config

TIMESTAMP_PATTERN = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)'


def process_zip_files(zip_path):
    """
    Read a ZIP archive containing .csv and .log files and return two dicts.

    Args:
        zip_path (str): full path of the ZIP archive.

    Returns:
        tuple: (csv_data, log_data)
               - csv_data (dict): key=file name, value=pandas.DataFrame.
               - log_data (dict): key=node address, value=log content string.
    """
    csv_data = {}
    log_data = {}

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for filename in zf.namelist():
                if filename.endswith('/') or filename.startswith('__MACOSX'):
                    continue

                _, extension = os.path.splitext(filename)

                if extension.lower() == '.csv':
                    with zf.open(filename) as file_obj:
                        try:
                            df = pd.read_csv(file_obj)
                            csv_data[filename] = df
                        except Exception as e:
                            print(f"Error reading CSV {filename}: {e}")

                elif extension.lower() == '.log':
                    with zf.open(filename, 'r') as file_obj:
                        try:
                            content = file_obj.read().decode('utf-8')
                            filename = filename.replace('.log', '')
                            filename = filename.split('_')[-1]
                            filename = config.default_address + filename + config.default_port
                            log_data[filename] = content
                        except Exception as e:
                            print(f"Error reading LOG {filename}: {e}")

    except FileNotFoundError:
        print(f"Error: ZIP file not found at the given path: {zip_path}")
        return {}, {}
    except zipfile.BadZipFile:
        print(f"Error: the file is not a valid ZIP archive or is corrupted: {zip_path}")
        return {}, {}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {}, {}

    return csv_data, log_data


def parse_log(log_data_input):
    """
    Scan the node log contents for the configured search string
    (config.log_search_key) and extract the timestamps of the matching lines.

    Args:
        log_data_input (dict): key=node address, value=log content string.

    Returns:
        dict: key=node address, value=list of timestamp strings.
    """
    timestamp_data = {}

    for file_name, content_log in log_data_input.items():
        timestamp_list = []

        rows = content_log.splitlines()

        for row in rows:
            if config.log_search_key in row:
                match = re.search(TIMESTAMP_PATTERN, row)

                if match:
                    timestamp = match.group(1)
                    timestamp_list.append(timestamp)

        timestamp_data[file_name] = timestamp_list

    return timestamp_data


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


# Duration of one epoch (client round), in seconds. The convergence clients run
# `rounds` rounds of `roundDuration` seconds each (see convergence_test/clients);
# epochs are therefore fixed 15 s windows measured from the experiment start.
ROUND_DURATION_S = 15.0


def parse_dfs(csv_data: Dict[str, pd.DataFrame], parsed_log=None):
    """
    Assign each CSV row an epoch (Group) as a fixed-size time window measured
    from the global experiment start, matching the clients' round structure.

    This is robust and deterministic: it does not depend on platform log
    timestamps (which may be stale or missing in an archive). The second
    argument is accepted for backward compatibility and ignored.
    """
    # Pass 1: parse StartTime and find the global experiment start (t0)
    parsed = []
    global_start = None

    for filename, current_df in csv_data.items():
        if hasattr(config, 'ignored_functions') and config.ignored_functions:
            current_df = current_df[~current_df['FuncName'].isin(config.ignored_functions)]
        current_df = current_df.reset_index(drop=True)

        if 'ExecHost' not in current_df.columns or 'StartTime' not in current_df.columns:
            parsed.append((current_df, False))
            continue

        try:
            current_df['StartTime_dt'] = pd.to_datetime(current_df['StartTime'], format='ISO8601', utc=True)
        except Exception as e:
            print(f"\033[91mError: skipping {filename}: cannot parse the 'StartTime' format.\033[0m Error: {e}")
            parsed.append((current_df, False))
            continue

        if not current_df.empty:
            cmin = current_df['StartTime_dt'].min()
            if global_start is None or cmin < global_start:
                global_start = cmin
        parsed.append((current_df, True))

    # Pass 2: epoch = floor((StartTime - t0) / ROUND_DURATION_S)
    elaborated_dfs = []
    for current_df, ok in parsed:
        if not ok or global_start is None:
            elaborated_dfs.append(current_df)
            continue

        delta_s = (current_df['StartTime_dt'] - global_start).dt.total_seconds()
        current_df['Group'] = (delta_s // ROUND_DURATION_S).clip(lower=0).astype(int)

        current_df['Duration'] = current_df['FuncDuration'] / 1000.0
        current_df['StartTime'] = pd.to_datetime(current_df['StartTime'])
        current_df['Is_Local'] = current_df['EntryHost'] == current_df['ExecHost']
        current_df = current_df.drop(columns=['StartTime_dt'])

        current_df = current_df.sort_values(by=['Group', 'StartTime']).reset_index(drop=True)
        elaborated_dfs.append(current_df)

    return elaborated_dfs
