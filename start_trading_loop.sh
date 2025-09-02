#!/bin/bash
# Boucle infinie pour exécuter le trading system toutes les 15 minutes
# Version robuste avec gestion d'erreurs et logging

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
LOG_FILE="$SCRIPT_DIR/trading_loop.log"
MAX_RETRIES=3
RETRY_COUNT=0

# Fonction de logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Fonction de gestion d'erreur
handle_error() {
    local exit_code=$1
    RETRY_COUNT=$((RETRY_COUNT + 1))
    
    log "❌ Erreur détectée (code: $exit_code, tentative: $RETRY_COUNT/$MAX_RETRIES)"
    
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        log "🛑 Nombre maximum de tentatives atteint. Attente de 5 minutes avant reprise..."
        sleep 300  # 5 minutes
        RETRY_COUNT=0
    else
        log "🔄 Nouvelle tentative dans 30 secondes..."
        sleep 30
    fi
}

# Piège pour gérer l'arrêt propre
trap 'log "🛑 Signal d'\''arrêt reçu. Arrêt du trading loop..."; exit 0' SIGTERM SIGINT

log "🚀 Démarrage du Trading Loop robuste"
log "📁 Répertoire: $SCRIPT_DIR"

while true; do
    current_hour=$((10#$(date +%H)))  # Force base 10
    current_day=$(date +%u)  # 1=lundi, 7=dimanche
    
    # Vérifier si c'est un jour ouvrable (lundi à vendredi)
    if [[ $current_day -ge 1 && $current_day -le 5 ]]; then
        # Vérifier si c'est pendant les heures de marché (14h30-21h UTC)
        if [[ $current_hour -ge 14 && $current_hour -le 21 ]]; then
            log "🔄 Exécution du système de trading... (${current_hour}h UTC)"
            
            if "$SCRIPT_DIR/run_trading_system.sh"; then
                log "✅ Exécution réussie"
                RETRY_COUNT=0  # Reset compteur en cas de succès
            else
                handle_error $?
                continue  # Reprendre la boucle sans attendre 15 minutes
            fi
        else
            # Log seulement toutes les heures en dehors des heures de marché
            if [ $((current_hour % 2)) -eq 0 ] && [ $(date +%M) -lt 15 ]; then
                log "💤 Hors heures de marché (${current_hour}h UTC)"
            fi
        fi
    else
        # Log seulement le dimanche soir pour éviter le spam
        if [ $current_day -eq 7 ] && [ $current_hour -eq 20 ] && [ $(date +%M) -lt 15 ]; then
            log "🏖️ Weekend - pas de trading"
        fi
    fi
    
    # Attendre 15 minutes
    sleep 900
done
