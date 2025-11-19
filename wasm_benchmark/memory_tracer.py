import sys
import time
import psutil
import subprocess
import csv
import argparse

def trace_synced_process(command, output_file):
    """
    Esegue un comando, ascolta il suo stdout per "SYNC_POINT"
    e misura la memoria RSS ad ogni SYNC_POINT.
    """

    # Avvia il processo, catturando stdout
    try:
        proc = subprocess.Popen(command,
                                stdout=subprocess.PIPE,
                                stdin=subprocess.PIPE,
                                stderr=subprocess.PIPE, # Cattura anche stderr per il debug
                                text=True, # Decodifica come testo (UTF-8)
                                bufsize=1) # Buffering a livello di riga
    except Exception as e:
        print(f"Errore nell'avvio del processo: {e}", file=sys.stderr)
        sys.exit(1)

    # Ottieni l'handle del processo psutil
    try:
        p = psutil.Process(proc.pid)
    except psutil.NoSuchProcess:
        print(f"Errore: Impossibile trovare il processo con PID {proc.pid}", file=sys.stderr)
        proc.kill()
        sys.exit(1)

    records = []
    execution_count = 0
    start_time = time.time()

    print(f"Tracer avviato. In ascolto di 'SYNC_POINT' da PID {proc.pid}...")

    # Leggi stdout riga per riga IN TEMPO REALE
    for line in iter(proc.stdout.readline, ''):
        line_str = line.strip()

        if line_str == "SYNC_POINT":
            execution_count += 1
            try:
                # MISURA LA MEMORIA RSS (Padre + Figli)
                current_rss = p.memory_info().rss
                children = p.children(recursive=True)
                for child in children:
                    try:
                        current_rss += child.memory_info().rss
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                elapsed = time.time() - start_time
                rss_mb = current_rss / 1024 / 1024

                # Aggiungi al record
                records.append((execution_count, elapsed, rss_mb))

                # 2. INVIA L'"ACK" A GO PER CONTINUARE
                proc.stdin.write("ACK\n")
                proc.stdin.flush()

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print("Errore: Processo perso durante la misurazione.", file=sys.stderr)
                break

        elif line_str: # Stampa qualsiasi altra cosa (debug)
            print(f"[Go STDOUT]: {line_str}", file=sys.stderr)

    # Il processo è terminato, leggi stderr per eventuali errori Go
    stderr_output = proc.stderr.read()
    if stderr_output:
        print(f"--- Output Stderr dal Test Go ---", file=sys.stderr)
        print(stderr_output, file=sys.stderr)
        print(f"---------------------------------", file=sys.stderr)

    # Scrivi tutti i record su CSV in una volta sola
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Execution_N", "Time_s", "RSS_MB"])
        writer.writerows(records)

    print(f"Tracer completato. Dati salvati in {output_file}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Output CSV file")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to run")

    args = parser.parse_args()

    if not args.command:
        print("Error: No command provided to run.", file=sys.stderr)
        sys.exit(1)

    if args.command[0] == "--":
        args.command.pop(0)

    trace_synced_process(args.command, args.output)

if __name__ == "__main__":
    main()