# 🚀 Trading Monitor - Système de Surveillance Automatisé

Système complet de monitoring pour le DataForSEO tracker avec surveillance TipRanks en temps réel.

## 🎯 Fonctionnalités

### ⏰ Scheduling Automatique
- **09h00** : Rapport quotidien complet (pré-ouverture EU)
- **15h30** : Check ouverture NYSE (9h30 EST)
- **18h00** : Check mi-session US
- **22h00** : Check post-clôture US (16h EST)
- **15h30-22h** : Vérifications toutes les 30min pendant le trading

### 🚨 Alertes Intelligentes
- **Changement de consensus** : Buy ↔ Hold ↔ Sell
- **Mouvements d'analystes** : ±5 analystes changent d'avis
- **Shifts importants** : ±3 recommandations Buy/Sell
- **Emails instantanés** sur changements majeurs

### 📊 Données Suivies
- Recommandations TipRanks (Buy/Hold/Sell)
- Consensus des analystes
- Nombre total d'analystes par action
- Évolution des positions SEO

## 🚀 Installation et Démarrage

### Option 1: Daemon Python (Recommandé)
```bash
# Démarrage automatique
./start_monitoring.sh

# Arrêt
./stop_monitoring.sh
```

### Option 2: Tâches Cron
```bash
# Configuration des tâches cron
./setup_cron.sh

# Désinstallation
crontab -e  # Supprimer les lignes trading_monitor
```

## 📋 Commandes Manuelles

### Vérification Immédiate
```bash
python3 trading_monitor.py --check-now
```

### Rapport Immédiat
```bash
python3 trading_monitor.py --report-now
```

### Mode Daemon (Manuel)
```bash
python3 trading_monitor.py --daemon
```

## 📁 Structure des Fichiers

```
├── trading_monitor.py          # Script principal de monitoring
├── start_monitoring.sh         # Démarrage automatique
├── stop_monitoring.sh          # Arrêt du monitoring
├── setup_cron.sh              # Configuration cron alternative
├── logs/
│   ├── monitoring.log         # Logs du daemon Python
│   ├── cron.log              # Logs des tâches cron
│   └── trading_system.log    # Logs du système de trading
├── trading_monitor_data.json  # Données historiques (auto-généré)
└── monitoring.pid             # PID du daemon (auto-généré)
```

## ⚙️ Configuration

Le système utilise automatiquement votre configuration existante :
- `dataforseo_config.json` : Configuration SEO et email
- Détection automatique des tickers dans vos mots-clés
- Intégration avec le système TipRanks existant

## 🔍 Exemples d'Alertes

### Changement de Consensus
```
🚨 ALERTE - Changements TipRanks
📈 AAPL
Consensus: Hold → Buy
Buy: 12 → 16 (+4)
Hold: 8 → 6 (-2)  
Sell: 2 → 0 (-2)
```

### Mouvement d'Analystes
```
🚨 ALERTE - Changements TipRanks
📈 TSLA  
Buy: 15 → 20 (+5)
Hold: 10 → 8 (-2)
Sell: 3 → 0 (-3)
```

## 📊 Planning Optimisé

Le système est synchronisé avec les horaires de la bourse américaine :

| Heure (CET) | Heure (EST) | Action |
|-------------|-------------|---------|
| 09h00 | 03h00 | Rapport quotidien complet |
| 15h30 | 09h30 | 🔔 Ouverture NYSE/NASDAQ |
| 18h00 | 12h00 | Check mi-session |
| 22h00 | 16h00 | 🔔 Clôture marchés US |

## 🛠️ Dépannage

### Le monitoring ne démarre pas
```bash
# Vérifier les dépendances
pip install schedule requests

# Vérifier la configuration
python3 dataforseo_tracker.py --test
```

### Pas d'alertes reçues
1. Vérifier la config email dans `dataforseo_config.json`
2. Vérifier les logs : `tail -f logs/monitoring.log`
3. Test manuel : `python3 trading_monitor.py --check-now`

### Processus zombie
```bash
# Nettoyer les processus
./stop_monitoring.sh
pkill -f trading_monitor.py
```

## 📧 Format des Alertes

Les alertes sont envoyées par email avec :
- **Sujet** : `🚨 ALERTE TipRanks - X changement(s) majeur(s)`
- **Contenu HTML** avec comparaisons avant/après
- **Horodatage** précis des changements
- **Codes couleur** pour identification rapide

## 🔐 Sécurité

- Données stockées localement dans `trading_monitor_data.json`
- Rate limiting automatique des appels API
- Gestion d'erreurs robuste
- Logs détaillés pour audit

## 📈 Performance

- **CPU** : Très faible (checks périodiques)
- **RAM** : ~50MB en mode daemon
- **Réseau** : Minimal (API calls TipRanks)
- **Stockage** : ~1MB pour les données historiques

---

🎯 **Le système surveille maintenant vos actions en temps réel et vous alerte instantanément sur les changements importants !**