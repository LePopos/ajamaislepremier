#!/bin/bash

# Script de gestion du service Trading System
SERVICE_NAME="trading-system"

case "$1" in
    start)
        echo "🚀 Démarrage du service Trading System..."
        sudo systemctl start $SERVICE_NAME
        sudo systemctl status $SERVICE_NAME --no-pager
        ;;
    stop)
        echo "🛑 Arrêt du service Trading System..."
        sudo systemctl stop $SERVICE_NAME
        ;;
    restart)
        echo "🔄 Redémarrage du service Trading System..."
        sudo systemctl restart $SERVICE_NAME
        sudo systemctl status $SERVICE_NAME --no-pager
        ;;
    status)
        sudo systemctl status $SERVICE_NAME --no-pager
        ;;
    logs)
        echo "📝 Logs du service (Ctrl+C pour quitter):"
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    install)
        echo "🔧 Installation du service..."
        if [[ $EUID -eq 0 ]]; then
            ./install_service.sh
        else
            sudo ./install_service.sh
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|install}"
        echo ""
        echo "Commandes disponibles:"
        echo "  start   - Démarre le service"
        echo "  stop    - Arrête le service"
        echo "  restart - Redémarre le service"
        echo "  status  - Affiche le statut du service"
        echo "  logs    - Affiche les logs en temps réel"
        echo "  install - Installe le service (nécessite sudo)"
        exit 1
        ;;
esac