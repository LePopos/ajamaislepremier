#!/bin/bash

# Script de démarrage du système de monitoring trading
# Usage: ./start_monitoring.sh

echo "🚀 Démarrage du système de monitoring trading..."

# Vérifier que Python et les dépendances sont installés
python3 -c "import schedule, requests" 2>/dev/null || {
    echo "❌ Erreur: Dépendances manquantes. Installation..."
    pip install schedule requests
}

# Vérifier que le fichier de configuration existe
if [ ! -f "dataforseo_config.json" ]; then
    echo "⚠️ Fichier dataforseo_config.json manquant. Création du template..."
    python3 dataforseo_tracker.py --help > /dev/null 2>&1 || {
        echo "❌ Impossible de créer le fichier de config. Lancez d'abord: python3 dataforseo_tracker.py"
        exit 1
    }
fi

# Créer le répertoire des logs s'il n'existe pas
mkdir -p logs

echo "📅 Planning automatique configuré:"
echo "   • 09h00 : Rapport quotidien complet"
echo "   • 15h30 : Check ouverture NYSE (9h30 EST)"  
echo "   • 18h00 : Check mi-session"
echo "   • 22h00 : Check post-clôture (16h EST)"
echo "   • 15h30-22h : Vérifications toutes les 30min"
echo ""
echo "🚨 Alertes automatiques sur:"
echo "   • Changement de consensus (Buy/Hold/Sell)"
echo "   • +/-5 analystes changent d'avis"
echo "   • Mouvements significatifs"
echo ""

# Lancer le monitoring
echo "✅ Lancement du monitoring en arrière-plan..."

# Option 1: Mode daemon Python (recommandé)
nohup python3 trading_monitor.py --daemon > logs/monitoring.log 2>&1 &
DAEMON_PID=$!

echo "✅ Monitoring démarré (PID: $DAEMON_PID)"
echo "📝 Logs: logs/monitoring.log"
echo ""
echo "📋 Commandes utiles:"
echo "   • Vérification immédiate: python3 trading_monitor.py --check-now"
echo "   • Rapport immédiat: python3 trading_monitor.py --report-now"
echo "   • Arrêter: kill $DAEMON_PID"
echo "   • Voir logs: tail -f logs/monitoring.log"

# Sauvegarder le PID pour pouvoir l'arrêter plus tard
echo $DAEMON_PID > monitoring.pid

echo ""
echo "🎯 Le système surveille maintenant vos actions en temps réel !"
echo "📧 Vous recevrez des alertes par email lors de changements importants."