import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import numpy as np

# ---------------------------------------------------------------------
# 1. Load benchmark data
# ---------------------------------------------------------------------

# Controlla se è stato fornito un argomento
if len(sys.argv) < 2:
    print("Errore: Per favore, fornisci il percorso del file di benchmark come argomento.")
    print("Usage: python script.py <path_to_benchmark_file>")
    sys.exit(1)

file_path = sys.argv[1]

# Open the file safely
try:
    with open(file_path, "r", encoding="utf-8") as f:
        benchmark_data = f.read()
except FileNotFoundError:
    print(f"Errore: File non trovato a '{file_path}'")
    sys.exit(1)

# ---------------------------------------------------------------------
# 2. Parse the Go benchmark data
# ---------------------------------------------------------------------
pattern = re.compile(
    # Cerca righe che iniziano con "BenchmarkExecutionTime_" e contengono "ns/op"
    r"^(BenchmarkExecutionTime_([A-Za-z0-9_]+)-\d+)\s+(\d+)\s+(\d+(?:\.\d+)?)\s+ns/op"
)

records = []
for line in benchmark_data.splitlines():
    match = pattern.search(line)
    if not match:
        continue

    full_tag = match.group(2)
    num_executions = int(match.group(3))
    ns_per_op = round(float(match.group(4)))

    # Estrai B/op e allocs/op se presenti
    b_op_match = re.search(r"(\d+)\s+B/op", line)
    allocs_op_match = re.search(r"(\d+)\s+allocs/op", line)

    bytes_per_op = int(b_op_match.group(1)) if b_op_match else 0
    allocs_per_op = int(allocs_op_match.group(1)) if allocs_op_match else 0

    parts = full_tag.split("_")
    runtime = parts[0].capitalize()
    compilation = "None"
    optimization = "None"
    algorithm_name = "Unknown"

    if len(parts) == 2: # Es: Native_Fibonacci
        algorithm_name = parts[1]
        compilation = "Native" # Etichetta più chiara
        optimization = "Native" # Etichetta più chiara
    elif len(parts) == 4: # Es: Wasmedge_AOT_NoOpts_Fibonacci
        compilation = parts[1].capitalize()
        optimization = parts[2] # No .capitalize() per preservare "NoOpts" e "WithOpts"
        algorithm_name = parts[3]
    else:
        print(f"Warning: Skipping unrecognized tag format: {full_tag}")
        continue

    # Aggiungi suffissi ai nomi degli algoritmi
    if "TailFibonacci" == algorithm_name:
        algorithm_name = algorithm_name + " (20k)"
    if "Fibonacci" == algorithm_name:
        algorithm_name = algorithm_name + " (40)"

    records.append({
        "Runtime": runtime,
        "Compilation": compilation,
        "Algorithm": algorithm_name,
        "Optimization": optimization,
        "Iterations": num_executions,
        "ns/op": ns_per_op,
        "B/op": bytes_per_op,
        "allocs/op": allocs_per_op,
    })

df = pd.DataFrame(records)
print("--- Dati di Benchmark Analizzati ---")
print(df)
print("-----------------------------------\n")

# ---------------------------------------------------------------------
# 3. Creazione Etichette e Ordinamento per i grafici
# ---------------------------------------------------------------------

# Etichetta X originale e completa (per il grafico della memoria)
df["X_label_original"] = df["Runtime"] + "\n" + df["Compilation"] + "\n" + df["Optimization"]
# Salva l'ordine originale per forzare il grafico
xaxis_order_original = df['X_label_original'].unique()


# Etichetta X più semplice (per i grafici temporali e di speedup)
def create_simple_label(row):
    if row["Runtime"].lower() == "native":
        return row["Runtime"]
    else:
        return f"{row['Runtime']}\n{row['Compilation']}"
df["X_label_simple"] = df.apply(create_simple_label, axis=1)
# Salva l'ordine originale per forzare i grafici
xaxis_order_simple = df['X_label_simple'].unique()


# Ordina gli algoritmi in modo univoco per forzare la coerenza dei colori
all_algorithms = sorted(df['Algorithm'].unique())

# ---------------------------------------------------------------------
# 4. Visualization setup
# ---------------------------------------------------------------------
sns.set_theme(style="whitegrid", font_scale=1.2)
palette = "Set2"

# ---------------------------------------------------------------------
# 5. Creazione Figura Combinata (Layout 2x2 personalizzato)
# ---------------------------------------------------------------------
# figsize più largo (20) e un po' più corto (16)
fig = plt.figure(figsize=(20, 16))
fig.suptitle("Analisi Tempo di Esecuzione e Speedup", fontsize=18, y=0.98)

# Griglia 2x2: 2 grafici in alto, 1 grafico che si estende in basso
ax1 = plt.subplot2grid((2, 2), (0, 0)) # Riga 0, Col 0
ax2 = plt.subplot2grid((2, 2), (0, 1)) # Riga 0, Col 1
ax3 = plt.subplot2grid((2, 2), (1, 0), colspan=2) # Riga 1, Col 0, esteso per 2 colonne

# --- Plot 1: Average Execution Time (NO Optimizations) ---
# Filtra per NoOpts + baselines (Native)
df_no_opts = df[df["Optimization"].isin(["NoOpts", "Native"])]

sns.barplot(
    data=df_no_opts,
    x="X_label_simple",
    y="ns/op",
    hue="Algorithm",
    palette=palette,
    ax=ax1,
    hue_order=all_algorithms, # Forza coerenza colori
    order=xaxis_order_simple  # Forza coerenza ordine X
)

ax1.set_yscale("log")
ax1.set_title("Average Execution Time - NO Optimizations (log scale)")
ax1.set_ylabel("ns/op (log scale)")
ax1.set_xlabel("") # Rimuovi etichetta X
ax1.tick_params(axis="x", labelsize=12)
# Salva gli handle della legenda dal primo grafico (che include "Native")
handles, labels = ax1.get_legend_handles_labels()
ax1.legend_.remove() # Rimuovi legenda per unire più tardi

# --- Plot 2: Average Execution Time (WITH Optimizations) ---
# Filtra per WithOpts + baselines (Native)
df_with_opts = df[df["Optimization"].isin(["WithOpts", "Native"])]

sns.barplot(
    data=df_with_opts,
    x="X_label_simple",
    y="ns/op",
    hue="Algorithm",
    palette=palette,
    ax=ax2,
    hue_order=all_algorithms, # Forza coerenza colori
    order=xaxis_order_simple  # Forza coerenza ordine X
)

ax2.set_yscale("log")
ax2.set_title("Average Execution Time - WITH Optimizations (log scale)")
ax2.set_ylabel("") # Rimuovi etichetta Y
ax2.set_xlabel("") # Rimuovi etichetta X
ax2.tick_params(axis="x", labelsize=12)
ax2.legend_.remove() # Rimuovi legenda

# --- Plot 3: Speedup (NoOpts / WithOpts) ---

# Aggrega i dati prima del pivot per ottenere la media
df_avg = df.groupby(["Algorithm", "Runtime", "Compilation", "Optimization"])["ns/op"].mean().reset_index()

# Pivot table per ottenere NoOpts e WithOpts affiancati
df_pivot = df_avg.pivot_table(
    index=["Algorithm", "Runtime", "Compilation"],
    columns="Optimization",
    values="ns/op"
).reset_index()

# Calcola speedup solo se entrambe le colonne esistono
if "NoOpts" in df_pivot.columns and "WithOpts" in df_pivot.columns:
    df_pivot["Speedup"] = df_pivot["NoOpts"] / df_pivot["WithOpts"]

    # Crea l'etichetta semplice per i dati pivot
    df_pivot["X_label_simple"] = df_pivot.apply(create_simple_label, axis=1)

    # Filtra solo le righe dove lo speedup è stato calcolato
    df_speedup = df_pivot.dropna(subset=["Speedup"])

    sns.barplot(
        data=df_speedup,
        x="X_label_simple",
        y="Speedup",
        hue="Algorithm",
        palette=palette,
        ax=ax3,
        hue_order=all_algorithms, # Forza coerenza colori
        order=xaxis_order_simple  # Forza coerenza ordine X
    )

    # Aggiungi una linea a y=1.0 per riferimento
    line = ax3.axhline(y=1.0, color='k', linestyle='--', label='No Speedup (1.0x)')

    ax3.set_title("Speedup (Tempo NoOpts / Tempo WithOpts)")
    ax3.set_ylabel("Fattore di Speedup (Maggiore è, meglio è)")
    ax3.set_xlabel("Runtime")
    ax3.tick_params(axis="x", labelsize=12)

    # Rimuovi la legenda specifica di ax3
    ax3.legend_.remove()

    # Aggiungi la linea di speedup agli handle salvati
    handles.append(line)
    labels.append(line.get_label())

    print("Grafico speedup generato come parte di fig1_combined_time_plots.png")
else:
    print("Warning: Colonne 'NoOpts' o 'WithOpts' non trovate dopo il pivot. Salto il grafico di speedup.")
    ax3.set_title("Speedup (Dati non disponibili)")
    ax3.text(0.5, 0.5, "Impossibile calcolare lo speedup (dati mancanti)",
             horizontalalignment='center', verticalalignment='center',
             transform=ax3.transAxes, color='red')

# --- Legenda Globale e Salvataggio ---

# Calcola il numero di colonne per la legenda
num_labels = len(labels)
# Prova a mettere un massimo di 6 elementi per riga
ncol = min(num_labels, 6)

# Aggiungi la legenda globale in basso alla FIGURA
fig.legend(
    handles=handles,
    labels=labels,
    title="Algorithm",
    loc='lower center',          # Posiziona in basso al centro
    bbox_to_anchor=(0.5, 0.02),  # (0.5=centro X, 0.02=vicino al fondo Y)
    borderaxespad=0.1,
    ncol=ncol                    # Numero di colonne
)

# Aggiusta il layout per fare spazio alla legenda in basso e al titolo in alto
plt.subplots_adjust(
    top=0.92,    # Spazio per suptitle
    bottom=0.15, # Spazio sufficiente per la legenda in basso
    left=0.05,
    right=0.98,
    hspace=0.35, # Spazio verticale tra righe di grafici
    wspace=0.1   # Spazio orizzontale tra grafici affiancati
)

plt.savefig("fig1_combined_time_plots.png")
plt.close(fig) # Chiudi la figura combinata


# ---------------------------------------------------------------------
# 8. Plot 4: Memory Usage (Come l'originale fig2.png) - SEPARATO
# ---------------------------------------------------------------------
plt.figure(figsize=(15, 6)) # Aumentata la larghezza per le etichette
sns.barplot(
    data=df,
    x="X_label_original", # Usa l'etichetta X originale completa
    y="B/op",
    hue="Algorithm",
    palette=palette,
    hue_order=all_algorithms, # Forza coerenza colori
    order=xaxis_order_original # Forza coerenza ordine X
)
plt.yscale("log")
plt.title("Average Memory Usage per Runtime (B/op)")
plt.ylabel("Bytes per Operation (log scale)")
plt.xlabel("Configurazione Runtime") # Etichetta aggiornata
plt.xticks(fontsize=10) # Rimpicciolito il font per evitare sovrapposizioni
plt.legend(
    title="Algorithm",
    bbox_to_anchor=(1.02, 1),
    loc="upper left",
    borderaxespad=0
)
plt.tight_layout()
plt.savefig("fig2_memory.png")
plt.close()

print("\n--- Processo completato ---")
print("Grafici generati:")
print("- fig1_combined_time_plots.png (Grafici tempi e speedup combinati)")
print("- fig2_memory.png (Utilizzo memoria)")
print("------------------------------")