import pandas as pd
import os
import zipfile
import re
import sys
from datetime import datetime
import pytz
from typing import Dict, List

# Import custom config
import config

def processa_zip_files(zip_path):
    """
    Legge un file ZIP contenente file .csv e .log e restituisce due dizionari.

    Args:
        zip_path (str): Il percorso completo del file ZIP.

    Returns:
        tuple: Una tupla contenente (dati_csv, dati_log).
               - dati_csv (dict): Chiave=nome_file, Valore=pandas.DataFrame.
               - dati_log (dict): Chiave=nome_file, Valore=contenuto_stringa.
    """
    dati_csv = {}
    dati_log = {}

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for filename in zf.namelist():
                if filename.endswith('/') or filename.startswith('__MACOSX'):
                    continue

                nome_base, estensione = os.path.splitext(filename)

                if estensione.lower() == '.csv':
                    with zf.open(filename) as file_obj:
                        try:
                            df = pd.read_csv(file_obj)
                            dati_csv[filename] = df
                        except Exception as e:
                            print(f"Errore nella lettura del CSV {filename}: {e}")

                elif estensione.lower() == '.log':
                    with zf.open(filename, 'r') as file_obj:
                        try:
                            # Assumiamo la codifica UTF-8
                            content = file_obj.read().decode('utf-8')
                            filename = filename.replace('.log', '')
                            filename = filename.split('_')[-1]
                            filename = config.default_address + filename + config.default_port
                            dati_log[filename] = content
                        except Exception as e:
                            print(f"Errore nella lettura del LOG {filename}: {e}")

    except FileNotFoundError:
        print(f"Errore: File ZIP non trovato al percorso specificato: {zip_path}")
        return {}, {}
    except zipfile.BadZipFile:
        print(f"Errore: Il file non è un archivio ZIP valido o è corrotto: {zip_path}")
        return {}, {}
    except Exception as e:
        print(f"Si è verificato un errore inatteso: {e}")
        return {}, {}

    return dati_csv, dati_log


def parse_log(dati_log_input):
    """
    Analizza i contenuti dei file di log, cercando una stringa specifica, 'DEFAULT-STRONG-POLICY, transition to decision state'.
    Estrae i timestamp dalle righe che contengono tale stringa.

    Args:
        dati_log_input (dict): Dizionario con Chiave=nome_file, Valore=contenuto_stringa del log.

    Returns:
        dict: Dizionario con Chiave=nome_file, Valore=Lista di timestamp (stringhe).
    """
    timestamp_data = {}

    TIMESTAMP_PATTERN = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)'

    for nome_file, content_log in dati_log_input.items():
        list_timestamp = []

        righe = content_log.splitlines()

        for riga in righe:
            if config.log_search_key in riga:
                match = re.search(TIMESTAMP_PATTERN, riga)

                if match:
                    timestamp = match.group(1)
                    list_timestamp.append(timestamp)

        timestamp_data[nome_file] = list_timestamp

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

def parse_dfs(dati_csv: Dict[str, pd.DataFrame], dati_timestamp_per_ip: Dict[str, List[str]]):
    """
    Elabora i DataFrame CSV assegnando a ciascuna riga un gruppo basato sui timestamp di transizione estratti dai log.
    """
    elaborated_dfs = []

    ip_windows: Dict[str, List[datetime]] = {}

    for ip, timestamps in dati_timestamp_per_ip.items():
        try:
            #print(timestamps)
            sorted_dt = sorted([
                parse_timestamp(ts)
                for ts in timestamps
            ])
            #print(sorted_dt)
            ip_windows[ip] = sorted_dt
        except ValueError as e:
            print(f"Skipping IP {ip}: Errore nel parsing del formato dei timestamp di log. Errore: {e}")
            ip_windows[ip] = []

    for filename, current_df in dati_csv.items():

        if hasattr(config, 'ignored_functions') and config.ignored_functions:
            current_df = current_df[~current_df['FuncName'].isin(config.ignored_functions)]

        current_df = current_df.reset_index(drop=True)

        if 'ExecHost' not in current_df.columns or 'StartTime' not in current_df.columns:
            elaborated_dfs[filename] = current_df
            continue

        try:
            current_df['StartTime_dt'] = pd.to_datetime(current_df['StartTime'], format='ISO8601', utc=True)
        except Exception as e:
            print(f"\033[91mError: Skipping {filename}: Errore nel parsing del formato 'StartTime'.\033[0m Errore: {e}")
            elaborated_dfs[filename] = current_df
            continue

        def get_window_group(row):
            exec_host = row['ExecHost']
            start_time = row['StartTime_dt']

            if exec_host not in ip_windows or not ip_windows[exec_host]:
                print(f"\033[91mError: ExecHost {row['ExecHost']} has no defined windows. Assigned to Group -1.\033[0m")
                return -1  # Nessuna finestra definita per questo host

            windows = ip_windows[exec_host]

            # Confronto tra datetimes AWARE in UTC
            for i, window_ts in enumerate(windows):
                if start_time < window_ts:
                    return i

            print(
                f"\033[93mWarning: ExecHost {row['ExecHost']} assigned after last window. {row['StartTime']} - {row['FuncName']} on {row['EntryHost']}\033[0m")
            return len(windows)

        current_df['Group'] = current_df.apply(get_window_group, axis=1)

        current_df['Duration'] = current_df['FuncDuration'].astype(str).str.replace('ms', '').astype(float)
        current_df['StartTime'] = pd.to_datetime(current_df['StartTime'])
        current_df['Is_Local'] = current_df['EntryHost'] == current_df['ExecHost']
        current_df = current_df.drop(columns=['StartTime_dt'])

        current_df = current_df.sort_values(by=['Group', 'StartTime']).reset_index(drop=True)

        elaborated_dfs.append(current_df)
    return elaborated_dfs


def find_equilibrium_timestamp(dfs):
    """
    Find the equilibrium timestamp across multiple DataFrames.
    """
    min_timestamps = []
    for df in dfs:
        for index, row in df.iterrows():
            if row['FuncName'] + "-" + row['EntryHost'] in config.eq_map and row['ExecHost'] == config.eq_map[
                row['FuncName'] + "-" + row['EntryHost']]:
                min_timestamps.append(row['StartTime'])
                break

    if not min_timestamps:
        for df in dfs:
            df['BeforeEq'] = False
        return dfs, None

    equilibrium_ts = pd.to_datetime(max(min_timestamps))

    group_max_s = set()
    for df in dfs:
        df['StartTime'] = pd.to_datetime(df['StartTime'])

        group_max = df.groupby('Group')['StartTime'].transform('min')
        group_max_s.update(group_max)

        df['BeforeEq'] = group_max <= equilibrium_ts

    return dfs, equilibrium_ts