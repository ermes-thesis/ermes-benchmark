import os

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import MaxNLocator


def process_scenario(scenario_name, base_input_dir, base_output_dir, files=None, filters=None):
    """
    Elabora un singolo scenario (es. 'static_users' o 'moving_users').
    Legge i 3 CSV dalla cartella di input e salva i grafici nella cartella di output.
    """

    # Costruzione percorsi
    input_dir = os.path.join(base_input_dir, scenario_name)
    output_dir = os.path.join(base_output_dir, scenario_name)

    print(f"\n--- Elaborazione Scenario: {scenario_name} ---")
    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")

    # Creazione cartella output se non esiste
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # file map
    if not files:
        files_to_load = [
            f for f in os.listdir(input_dir)
            if f.lower().endswith(".csv")
        ]
    else:
        files_to_load = files

    file_map = {fname: os.path.splitext(fname)[0].replace("_", " ").title() for fname in files_to_load}

    # 1. Caricamento Dati
    all_data = []
    for fname, arch_label in file_map.items():
        file_path = os.path.join(input_dir, fname)

        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                df['Architecture'] = arch_label
                all_data.append(df)
                print(f"  ✅ Caricato: {fname}")
            except Exception as e:
                print(f"  ❌ Errore leggendo {fname}: {e}")
        else:
            print(f"  ⚠️ File non trovato: {fname}")

    if not all_data:
        print(f"  Nessun dato trovato per {scenario_name}. Passo al prossimo.")
        return

    # Unione DataFrame
    full_df = pd.concat(all_data, ignore_index=True)

    # Applicazione filtri AND
    if filters:
        mask = pd.Series(True, index=full_df.index)

        for col, expected_value in filters.items():
            if col not in full_df.columns:
                print(f"  ⚠️ Colonna filtro non trovata: {col}")
                continue

            # OR: lista di valori
            if isinstance(expected_value, (list, tuple, set)):
                mask &= full_df[col].isin(expected_value)
            # AND: valore singolo
            else:
                mask &= full_df[col] == expected_value

        full_df = full_df[mask]

        if full_df.empty:
            print("  ⚠️ Dataset vuoto dopo i filtri.")
            return

    # 2. Filtro Round
    if scenario_name == 'moving_users':
        full_df = full_df[full_df['Round'] <= 20]
    else:
        full_df = full_df[full_df['Round'] <= 10]

    # Verifica colonne
    required_cols = ['Users', 'Collections', 'Round', 'AverageLatency', 'Mode']
    if not all(col in full_df.columns for col in required_cols):
        print("  ❌ Errore: Colonne mancanti nel CSV.")
        return

    # 3. Raggruppamento e Plotting
    grouped_configs = full_df.groupby(['Users', 'Collections'])
    count = 0

    for (users, collections), group_df in grouped_configs:
        plt.figure(figsize=(10, 6))

        subgroups = group_df.groupby(['Architecture', 'Mode'])
        has_plotted = False

        for (arch, mode), sub_df in subgroups:
            if sub_df.empty: continue
            sub_df = sub_df.sort_values('Round')

            # Stili
            if arch == 'Centralized':
                color = 'tab:orange'
                marker = 'o'
            elif arch == 'Distributed':
                color = 'tab:blue'
                marker = '^'
            elif arch == 'Query Cache Disabled':
                color = 'tab:green'
                marker = 's'
            else:
                color = 'tab:gray'
                marker = 'd'

            mode_str = str(mode).lower()
            if 'sequential' in mode_str:
                linestyle = '-'
            elif 'eventual' in mode_str:
                linestyle = '--'
            else:
                linestyle = ':'

            label_text = f"{arch} [{mode_str}]"

            plt.plot(sub_df['Round'], sub_df['AverageLatency'],
                     label=label_text, color=color, marker=marker,
                     linestyle=linestyle, linewidth=2, markersize=6)
            has_plotted = True

        if has_plotted:
            plt.xlabel('Round (Time)', fontweight='bold', fontsize=12)
            plt.ylabel('Average Latency (ms)', fontweight='bold', fontsize=12)
            #plt.title(f'Latency vs Round (Max 10) - {scenario_name}\n(Users: {users}, Collections: {collections})')
            plt.grid(True, linestyle='--', alpha=0.3)
            legend =plt.legend(title='Configuration', loc='best', fontsize=12)
            legend.get_title().set_fontweight('bold')
            plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
            plt.tight_layout()

            filename = f"u{users}_c{collections}.png"
            plt.savefig(os.path.join(output_dir, filename), dpi=300)
            count += 1

        plt.close()

    print(f"  ✅ Generati {count} grafici in {output_dir}")


def process_file_across_scenarios(
    file_name,
    base_input_dir,
    base_output_dir,
    scenarios,
    filters=None
):

    print(f"\n--- Elaborazione File: {file_name} ---")

    all_data = []

    # 1. Caricamento dati da tutti gli scenari
    for scenario in scenarios:
        file_path = os.path.join(base_input_dir, scenario, file_name)

        if not os.path.exists(file_path):
            print(f"  ⚠️ File non trovato: {file_path}")
            continue

        try:
            df = pd.read_csv(file_path)
            df["Scenario"] = scenario
            all_data.append(df)
            print(f"  ✅ Caricato: {scenario}/{file_name}")
        except Exception as e:
            print(f"  ❌ Errore leggendo {file_path}: {e}")

    if not all_data:
        print("  ❌ Nessun dato disponibile.")
        return

    full_df = pd.concat(all_data, ignore_index=True)

    # 2. Applicazione filtri AND
    if filters:
        mask = pd.Series(True, index=full_df.index)

        for col, expected_value in filters.items():
            if col not in full_df.columns:
                print(f"  ⚠️ Colonna filtro non trovata: {col}")
                continue

            # OR: lista di valori
            if isinstance(expected_value, (list, tuple, set)):
                mask &= full_df[col].isin(expected_value)
            # AND: valore singolo
            else:
                mask &= full_df[col] == expected_value

        full_df = full_df[mask]

        if full_df.empty:
            print("  ⚠️ Dataset vuoto dopo i filtri.")
            return
        
    # 3. Filtro Round per scenario
    def max_round(row):
        return 20 if row["Scenario"] == "moving_users" else 10

    full_df = full_df[full_df["Round"] <= full_df.apply(max_round, axis=1)]

    # 4. Output dir
    output_dir = os.path.join(base_output_dir, "by_file", file_name.replace(".csv", ""))
    os.makedirs(output_dir, exist_ok=True)

    # 5. Un grafico per ogni Collections
    grouped = full_df.groupby(["Users", "Mode"])
    count = 0

    
    for (users, mode), group_df in grouped:
        plt.figure(figsize=(10, 6))

        subgroups = group_df.groupby(['Scenario', 'Collections'])

        # Linee = (Users, Scenario)
        for (scenario, collections), sub_df in subgroups:
            if sub_df.empty: continue

            sub_df = sub_df.sort_values("Round")

            label = f"{collections}"

            plt.plot(
                sub_df["Round"],
                sub_df["AverageLatency"],
                label=label,
                linewidth=2,
                marker="o"
            )

        plt.xlabel("Round (Time)", fontweight='bold', fontsize=12)
        plt.ylabel("Average Latency (ms)", fontweight='bold', fontsize=12)
        #plt.title(
        #    f"Latency vs Round\n"
        #    f"users: {users}"
        #)
        plt.grid(True, linestyle="--", alpha=0.3)
        legend = plt.legend(title="Collections", fontsize=12)
        legend.get_title().set_fontweight('bold')
        plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
        plt.tight_layout()

        fname = f"u{users}_{mode}.png"
        plt.savefig(os.path.join(output_dir, fname), dpi=300)
        plt.close()

        count += 1

    print(f"  ✅ Generati {count} grafici in {output_dir}")

def main():
    # Percorsi Base
    base_data_dir = "data/rounds"
    base_out_dir = "output_img/rounds"
    files = [
        "distributed.csv",
        "centralized.csv",
    ]

    # Scenari da elaborare
    #scenarios = ["static_users", "moving_users"]
    scenarios = ["static_users"]


    for scenario in scenarios:
        process_scenario(scenario, base_data_dir, base_out_dir)#, files)

    csv_filters = {
        "Users": [256, 1024] #or 
    }
    files = [
        "distributed.csv",
    ]

    for file_name in files:
        process_file_across_scenarios(
            file_name,
            base_data_dir,
            base_out_dir,
            scenarios,
            csv_filters
        )



if __name__ == "__main__":
    main()
