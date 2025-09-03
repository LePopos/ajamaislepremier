#!/bin/bash

# 🎯 Script de configuration du déploiement automatique 
# À exécuter sur le droplet une seule fois pour configurer le déploiement auto

echo "⚙️ Configuration du déploiement automatique..."
echo "📍 Ce script configure le hook Git pour déploiement auto"

# Vérifier qu'on est sur le droplet dans le bon répertoire
if [[ ! -d "/opt/trading_system" ]]; then
    echo "❌ Répertoire /opt/trading_system non trouvé"
    echo "💡 Ce script doit être exécuté sur le droplet"
    exit 1
fi

cd /opt/trading_system

# Mettre à jour le repo avec les dernières modifications
echo "📥 Récupération des dernières modifications..."
git fetch origin
git checkout feature/gsc-analyzer
git pull origin feature/gsc-analyzer

# Créer un hook post-merge pour déclencher le déploiement automatique
echo "🔧 Installation du hook de déploiement automatique..."
mkdir -p .git/hooks

cat > .git/hooks/post-merge << 'HOOK_SCRIPT'
#!/bin/bash
# Hook Git qui se déclenche après un git pull/merge

echo "🎣 Hook post-merge déclenché!"

# Vérifier si les fichiers du trading system ont changé
if git diff --name-only HEAD@{1} HEAD | grep -E "(trading_system/|main\.py|requirements\.txt)"; then
    echo "🚀 Modifications détectées dans le trading system - déclenchement du déploiement..."
    
    cd trading_system
    
    # Exécuter le script de déploiement
    if [[ -f "deploy_hook.sh" ]]; then
        echo "▶️ Exécution du déploiement automatique..."
        ./deploy_hook.sh
    else
        echo "❌ Script deploy_hook.sh non trouvé"
    fi
    
else
    echo "ℹ️ Pas de modifications dans le trading system - pas de déploiement nécessaire"
fi
HOOK_SCRIPT

chmod +x .git/hooks/post-merge

echo "✅ Hook post-merge installé"

# Rendre le script de déploiement exécutable
chmod +x trading_system/deploy_hook.sh 2>/dev/null || echo "deploy_hook.sh sera créé au prochain pull"

# Créer un alias pour faciliter les déploiements manuels
echo "🔧 Création d'alias pour déploiements manuels..."
echo 'alias deploy-trading="cd /opt/trading_system/trading_system && ./deploy_hook.sh"' >> /root/.bashrc
echo 'alias update-trading="cd /opt/trading_system && git pull origin feature/gsc-analyzer"' >> /root/.bashrc

echo "✅ Configuration terminée !"
echo ""
echo "📋 DÉPLOIEMENT AUTOMATIQUE CONFIGURÉ :"
echo "  🎣 Hook Git installé - déploiement auto après git pull"
echo "  🔧 Alias créés :"
echo "    - 'update-trading' : met à jour le code"  
echo "    - 'deploy-trading' : déploie manuellement"
echo ""
echo "🚀 POUR DÉCLENCHER LE DÉPLOIEMENT MAINTENANT :"
echo "  cd /opt/trading_system && git pull origin feature/gsc-analyzer"
echo ""
echo "📊 Toutes les améliorations seront déployées automatiquement :"
echo "  ✅ Probabilités réalistes (25-75%)"
echo "  ✅ Graphiques avec vraies données Yahoo Finance"
echo "  ✅ Logique SELL améliorée"
echo "  ✅ Corrections bugs SQLAlchemy"
echo ""