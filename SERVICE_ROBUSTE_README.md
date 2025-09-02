# Service Trading System Robuste 🚀

## ✅ Problème résolu
Le système de trading ne tombera plus jamais grâce à :

### 1. **Service Systemd** (Auto-redémarrage)
- Redémarrage automatique en cas de crash
- Démarrage automatique au boot du système
- Logs centralisés via journald

### 2. **Gestion d'erreurs robuste**
- Retry automatique (3 tentatives)
- Délai progressif entre les tentatives
- Logs détaillés avec timestamps

### 3. **Monitoring intelligent**
- Réduction du spam de logs
- Signaux propres d'arrêt (SIGTERM/SIGINT)
- Compteur de retry avec reset

## 🎯 Commandes principales

### Installation du service (une seule fois)
```bash
sudo ./install_service.sh
```

### Gestion quotidienne
```bash
./manage_trading_service.sh status    # Voir l'état
./manage_trading_service.sh logs      # Voir les logs live
./manage_trading_service.sh restart   # Redémarrer si besoin
```

### Logs disponibles
- **Service systemd** : `sudo journalctl -u trading-system -f`
- **Application** : `tail -f trading_system/logs/trading_system.log`
- **Loop robuste** : `tail -f trading_loop.log`

## 📊 Fonctionnement

### Horaires de trading
- **Lundi à Vendredi** : 14h30 - 21h00 UTC
- **Intervalle** : Toutes les 15 minutes
- **Weekend** : Arrêt automatique

### En cas d'erreur
1. **Retry immédiat** (3 fois max)
2. **Pause 5 minutes** si échec répété  
3. **Reprise automatique**
4. **Service systemd redémarre** si crash total

## 🛠️ Files créés
- `trading-system.service` - Configuration systemd
- `install_service.sh` - Installation automatique
- `manage_trading_service.sh` - Gestion simplifiée  
- `start_trading_loop.sh` - Script robuste amélioré

## 🔥 Plus jamais de problème !
Le système est maintenant **bulletproof** et tournera en continu sans intervention.