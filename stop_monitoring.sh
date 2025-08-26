#!/bin/bash

# Script d'arrêt du système de monitoring trading
# Usage: ./stop_monitoring.sh

echo "🛑 Arrêt du système de monitoring..."

if [ -f "monitoring.pid" ]; then
    PID=$(cat monitoring.pid)
    if kill -0 "$PID" 2>/dev/null; then
        echo "⏹️ Arrêt du processus monitoring (PID: $PID)..."
        kill $PID
        sleep 2
        
        # Vérifier si le processus est vraiment arrêté
        if kill -0 "$PID" 2>/dev/null; then
            echo "🔨 Processus résistant, arrêt forcé..."
            kill -9 $PID
        fi
        
        echo "✅ Monitoring arrêté"
    else
        echo "⚠️ Processus déjà arrêté (PID $PID non trouvé)"
    fi
    
    rm -f monitoring.pid
else
    echo "⚠️ Pas de fichier PID trouvé"
    
    # Chercher le processus par nom
    PIDS=$(pgrep -f "trading_monitor.py --daemon")
    if [ ! -z "$PIDS" ]; then
        echo "🔍 Processus trouvés: $PIDS"
        echo "⏹️ Arrêt des processus..."
        echo $PIDS | xargs kill
        sleep 2
        echo "✅ Processus arrêtés"
    else
        echo "➡️ Aucun processus de monitoring trouvé"
    fi
fi

echo "🏁 Système de monitoring arrêté"