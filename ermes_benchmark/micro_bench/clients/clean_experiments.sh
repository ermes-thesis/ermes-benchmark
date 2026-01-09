#!/bin/bash

# --- CONFIGURAZIONE TARGET ---
# Stessi nodi definiti nel tuo run.sh
ERMES_NODES=("10.10.101.50" "10.10.101.51" "10.10.101.52" "10.10.101.53" "10.10.101.54" "10.10.101.55" "10.10.101.56" "10.10.101.57" "10.10.101.58")
JUMP_HOST="100.112.91.33"

# Funzione di pulizia
clean_remote_experiments() {
    echo "🧹 [Global Clean] Rimozione cartelle '/home/ubuntu/experiments_*' sui nodi remoti..."

    for NODE_IP in "${ERMES_NODES[@]}"; do
        # Usiamo 'sudo bash -s' per garantire i permessi di rimozione (spesso i log sono root:root)
        ssh -J ubuntu@${JUMP_HOST} -o StrictHostKeyChecking=no ubuntu@${NODE_IP} "sudo bash -s" << 'EOF'

        # Definiamo il pattern da cancellare
        TARGET_PATTERN="/home/ubuntu/experiments_*"

        # Controlliamo se esistono file/cartelle che corrispondono al pattern per evitare errori di 'rm'
        if ls $TARGET_PATTERN 1> /dev/null 2>&1; then
            rm -rf $TARGET_PATTERN
            echo "      🗑️  Cartelle experiments rimosse."
        else
            echo "      ℹ️  Nessuna cartella experiments trovata."
        fi
EOF
        echo "   ✅ ${NODE_IP} verificato."
    done
}

# Esecuzione
clean_remote_experiments
echo "🎉 Pulizia completata su tutti i nodi."