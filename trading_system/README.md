# TipRanks Trading System

Un système de trading automatisé qui suit les recommandations d'analystes de TipRanks.com et génère des signaux d'achat/vente automatiques pour les actions américaines.

## 🚀 Fonctionnalités

- **Collecte de données automatique** : Prix en temps réel (Alpha Vantage) + recommandations TipRanks
- **Génération de signaux intelligents** : Basée sur Smart Score, prix cibles et sentiment
- **Gestion des risques** : Stop-loss automatiques et dimensionnement de positions
- **Planificateur automatisé** : Collecte et analyse pendant les heures de marché
- **Base de données intégrée** : Historique complet des données et signaux

## 📋 Prérequis

1. **Clé API Alpha Vantage** (gratuite) : https://www.alphavantage.co/support/#api-key
2. **Python 3.8+**
3. **TipRanks** : Accès via API non-officielle (incluse)

## ⚙️ Installation

1. **Installer les dépendances** :
```bash
cd trading_system
pip install -r requirements.txt
```

2. **Configurer les variables d'environnement** :
```bash
cp .env.example .env
# Éditer .env avec vos clés API
```

3. **Variables essentielles dans `.env`** :
```env
ALPHA_VANTAGE_API_KEY=votre_cle_alpha_vantage
WATCHLIST=AAPL,MSFT,GOOGL,TSLA,NVDA,AMZN
MAX_POSITION_SIZE=1000.0
STOP_LOSS_PERCENTAGE=-5.0
```

## 🎯 Utilisation

### Commandes de base

```bash
# Vérifier la configuration
python main.py status --config-check

# Collecter les données une fois
python main.py collect

# Générer des signaux une fois  
python main.py signals

# Lancer le système automatisé
python main.py run
```

### Mode automatisé

Le système fonctionne automatiquement pendant les heures de marché (9h30-16h ET) :

- **Collecte de données** : Toutes les 15 minutes
- **Génération de signaux** : Toutes les 30 minutes  
- **Mise à jour des prix** : Toutes les 5 minutes
- **Nettoyage quotidien** : 18h ET
- **Nettoyage hebdomadaire** : Dimanche 2h

## 📊 Logique de trading

### Signaux d'achat (BUY)
- Smart Score ≥ 8/10
- Prix cible > prix actuel (+15%)
- Sentiment bullish dominant (>60%)
- Confiance ≥ 70%

### Signaux de vente (SELL)  
- Smart Score ≤ 3/10
- Prix cible < prix actuel (-10%)
- Sentiment bearish dominant (>60%)
- Confiance ≥ 70%

### Gestion des risques
- **Stop-loss** : -5% par défaut
- **Taille de position** : Basée sur la confiance
- **Exposition max** : $1000 par position par défaut
- **Limite quotidienne** : 10 trades max

## 📁 Structure du projet

```
trading_system/
├── config/
│   └── config.py           # Configuration centralisée
├── src/
│   ├── api/               
│   │   ├── tipranks_client.py      # Client TipRanks API
│   │   └── alpha_vantage_client.py # Client Alpha Vantage API
│   ├── models/
│   │   └── stock_models.py         # Modèles de données SQLAlchemy/Pydantic
│   └── services/
│       ├── data_collector.py       # Service collecte de données
│       ├── signal_generator.py     # Générateur de signaux
│       └── scheduler.py            # Planificateur automatisé
├── data/                   # Base de données SQLite
├── logs/                   # Fichiers de logs
├── main.py                # Point d'entrée principal
├── requirements.txt       # Dépendances Python
└── .env.example          # Template configuration
```

## 📈 Exemple de sortie

```
$ python main.py signals

Generating trading signals...

Generated 3 trading signals:

BUY signals (2):
  - AAPL: $182.50 (confidence: 0.85)
    Target: $195.00
    Stop Loss: $173.38
  - NVDA: $645.20 (confidence: 0.78)  
    Target: $720.00
    Stop Loss: $612.94

SELL signals (1):
  - TSLA: $248.42 (confidence: 0.72)
    Target: $220.00
    Stop Loss: $261.84
```

## ⚠️ Limitations et avertissements

- **Tests uniquement** : Ce système est conçu pour l'apprentissage et les tests
- **Pas de broker intégré** : Les signaux doivent être exécutés manuellement
- **Rate limiting** : Alpha Vantage limite à 500 requêtes/jour (gratuit)
- **TipRanks non-officiel** : L'API TipRanks n'est pas officielle
- **Heures de marché simplifiées** : Ne tient pas compte des jours fériés

## 🔧 Développement futur

- [ ] Intégration broker (Alpaca, Interactive Brokers)
- [ ] Interface web dashboard
- [ ] Backtesting historique
- [ ] Alertes email/SMS
- [ ] Plus d'indicateurs techniques
- [ ] Support crypto/forex

## 📄 Licence

Ce projet est à des fins éducatives uniquement. Utilisez à vos risques et périls.

## 🆘 Support

Pour les problèmes :
1. Vérifiez les logs dans `logs/trading_system.log`
2. Validez la configuration avec `python main.py status --config-check`
3. Testez les APIs individuellement