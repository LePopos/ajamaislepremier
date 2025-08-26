#!/bin/bash

# Script pour configurer les tâches cron (alternative au daemon Python)
# Usage: ./setup_cron.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📅 Configuration des tâches cron pour le trading monitor..."
echo "📁 Répertoire: $SCRIPT_DIR"

# Créer le fichier de cron temporaire
CRON_FILE=$(mktemp)

# Ajouter les tâches existantes (s'il y en a)
crontab -l 2>/dev/null > "$CRON_FILE" || true

# Supprimer les anciennes tâches de trading monitor
sed -i '/trading_monitor.py\|dataforseo_tracker.py/d' "$CRON_FILE"

# Ajouter les nouvelles tâches
cat >> "$CRON_FILE" << EOF

# === Trading Monitor - Système automatisé ===
# SEULEMENT LES JOURS DE SEMAINE (lun-ven) quand la bourse US est ouverte

# 09h00 : Rapport quotidien complet (pré-ouverture EU)
0 9 * * 1-5 cd $SCRIPT_DIR && python3 trading_monitor.py --report-now >> logs/cron.log 2>&1

# 15h30 : Check ouverture NYSE (9h30 EST)  
30 15 * * 1-5 cd $SCRIPT_DIR && python3 trading_monitor.py --check-now >> logs/cron.log 2>&1

# 18h00 : Check mi-session US
0 18 * * 1-5 cd $SCRIPT_DIR && python3 trading_monitor.py --check-now >> logs/cron.log 2>&1

# 22h00 : Check post-clôture US (16h EST)
0 22 * * 1-5 cd $SCRIPT_DIR && python3 trading_monitor.py --check-now >> logs/cron.log 2>&1

# Vérifications pendant les heures de trading US (16h-21h) - SEULEMENT SEMAINE
0 16,17,19,20,21 * * 1-5 cd $SCRIPT_DIR && python3 trading_monitor.py --check-now >> logs/cron.log 2>&1
30 16,17,19,20,21 * * 1-5 cd $SCRIPT_DIR && python3 trading_monitor.py --check-now >> logs/cron.log 2>&1

EOF

# Installer les nouvelles tâches cron
crontab "$CRON_FILE"

# Nettoyer le fichier temporaire
rm "$CRON_FILE"

# Créer le répertoire des logs
mkdir -p "$SCRIPT_DIR/logs"

echo "✅ Tâches cron configurées !"
echo ""
echo "📅 Planning configuré (LUNDI-VENDREDI uniquement):"
echo "   • 09h00 : Rapport quotidien complet"
echo "   • 15h30 : Check ouverture NYSE"
echo "   • 18h00 : Check mi-session"
echo "   • 22h00 : Check post-clôture"
echo "   • 16h-21h : Checks toutes les 30min"
echo ""
echo "🚫 Weekends et jours fériés US = PAS d'exécution"
echo ""
echo "📝 Logs: $SCRIPT_DIR/logs/cron.log"
echo ""
echo "📋 Commandes utiles:"
echo "   • Voir les tâches: crontab -l"
echo "   • Voir les logs: tail -f $SCRIPT_DIR/logs/cron.log"
echo "   • Test immédiat: python3 trading_monitor.py --check-now"
echo ""
echo "⚠️ Note: Les tâches cron nécessitent que le système reste allumé"
echo "💡 Alternative: Utilisez ./start_monitoring.sh pour un daemon Python"