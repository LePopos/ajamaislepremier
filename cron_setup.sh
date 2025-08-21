#!/bin/bash
# Script de configuration du cron pour le suivi SEO quotidien

echo "🔧 Configuration du cron pour le suivi SEO quotidien"
echo "=================================================="

# Chemin vers le script Python
SCRIPT_PATH=$(pwd)/dataforseo_tracker.py
LOG_PATH=$(pwd)/logs

# Créer le dossier de logs s'il n'existe pas
mkdir -p "$LOG_PATH"

# Vérifier que le script existe
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ Erreur: Le script $SCRIPT_PATH n'existe pas"
    exit 1
fi

# Rendre le script exécutable
chmod +x "$SCRIPT_PATH"

echo "📍 Script trouvé: $SCRIPT_PATH"
echo "📁 Logs dans: $LOG_PATH"

# Créer l'entrée cron (tous les jours à 9h00)
CRON_JOB="0 9 * * * /usr/bin/python3 $SCRIPT_PATH >> $LOG_PATH/seo_tracking.log 2>&1"

echo ""
echo "📅 Tâche cron à ajouter:"
echo "$CRON_JOB"
echo ""

# Demander confirmation
read -p "Voulez-vous ajouter cette tâche cron ? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Ajouter la tâche cron
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    
    echo "✅ Tâche cron ajoutée avec succès!"
    echo ""
    echo "📋 Tâches cron actuelles:"
    crontab -l
    
    echo ""
    echo "📝 Notes importantes:"
    echo "- Le script s'exécutera tous les jours à 9h00"
    echo "- Les logs sont sauvegardés dans: $LOG_PATH/seo_tracking.log"
    echo "- Pour modifier l'heure: crontab -e"
    echo "- Pour supprimer: crontab -r"
    echo ""
    echo "🔍 Vérifier les logs avec:"
    echo "tail -f $LOG_PATH/seo_tracking.log"
    
else
    echo "❌ Installation annulée"
    echo ""
    echo "Pour configurer manuellement:"
    echo "1. crontab -e"
    echo "2. Ajouter la ligne: $CRON_JOB"
fi

echo ""
echo "✅ Configuration terminée!"