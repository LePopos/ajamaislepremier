# Configuration GSC Analyzer

## 🚀 Installation

1. **Installer les dépendances :**
```bash
pip install -r requirements.txt
```

## 🔐 Configuration de l'authentification Google (Service Account)

### Étape 1: Google Cloud Console
1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créez un nouveau projet ou sélectionnez un existant
3. Activez l'**API Google Search Console** :
   - Dans le menu, allez à "APIs & Services" > "Library"
   - Recherchez "Google Search Console API"
   - Cliquez sur "Enable"

### Étape 2: Créer un Service Account
1. Allez à "APIs & Services" > "Credentials"
2. Cliquez "CREATE CREDENTIALS" > "Service account"
3. Configurez le Service Account :
   - **Service account name** : "gsc-analyzer" (ou autre)
   - **Service account ID** : sera généré automatiquement
   - **Description** : "Service account pour analyse GSC"
4. Cliquez "CREATE AND CONTINUE"
5. **Rôle** : Vous pouvez laisser vide pour l'instant
6. Cliquez "DONE"

### Étape 3: Générer la clé JSON
1. Dans la liste des Service Accounts, cliquez sur celui que vous venez de créer
2. Allez à l'onglet "Keys"
3. Cliquez "ADD KEY" > "Create new key"
4. Choisissez format "JSON"
5. **Téléchargez le fichier JSON** et renommez-le `service-account.json`
6. Placez `service-account.json` dans le dossier du script

### Étape 4: Ajouter le Service Account dans Search Console
1. Ouvrez le fichier JSON téléchargé et copiez l'email du service account (format : `nom@projet.iam.gserviceaccount.com`)
2. Allez sur [Google Search Console](https://search.google.com/search-console/)
3. Sélectionnez la propriété https://www.legrand.fr
4. Allez dans "Paramètres" > "Utilisateurs et autorisations"
5. Cliquez "AJOUTER UN UTILISATEUR"
6. Collez l'email du service account
7. Accordez au minimum les droits "Utilisateur avec restriction"
8. Cliquez "AJOUTER"

## 📊 Utilisation

### Commande de base :
```bash
python gsc_analyzer.py --credentials service-account.json
```

### Options avancées :
```bash
# Analyser sur 14 jours au lieu de 7
python gsc_analyzer.py --credentials service-account.json --days 14

# Récupérer top 1000 au lieu de 500
python gsc_analyzer.py --credentials service-account.json --top 1000

# Analyser un autre site
python gsc_analyzer.py --credentials service-account.json --site https://www.monsite.com

# Si votre fichier a un autre nom
python gsc_analyzer.py --credentials mon-service-account.json
```

## 📈 Ce que fait le script

### Filtres appliqués :
- **URLs en hausse** : Exclut les nouveaux contenus (0 clics précédemment)
- **URLs en baisse** : Exclut les contenus redirigés (0 clics actuellement)

### Données comparées :
- Période actuelle vs période précédente (même durée)
- Métriques : Clics, Impressions, CTR, Position moyenne

### Fichiers générés :
- `gsc_analysis_rising_YYYYMMDD_HHMMSS.csv` : URLs en hausse
- `gsc_analysis_falling_YYYYMMDD_HHMMSS.csv` : URLs en baisse

## 🔧 Paramètres par défaut

- **Site** : https://www.legrand.fr
- **Période** : 7 jours (comparé aux 7 jours précédents)
- **Top URLs** : 500 montantes + 500 descendantes
- **Limite API** : 25,000 rows par requête

## 🚨 Dépannage

### "Fichier service-account.json introuvable"
- Vérifiez que le fichier est dans le bon dossier
- Vérifiez l'orthographe du nom
- Utilisez le paramètre `--credentials` avec le bon chemin

### "Access denied" ou "Forbidden"
- Vérifiez que le service account est bien ajouté dans Google Search Console
- Vérifiez que l'email du service account est correct
- Assurez-vous que les droits "Utilisateur avec restriction" (minimum) sont accordés

### "API not enabled"
- Retournez dans Google Cloud Console
- Vérifiez que l'API Search Console est bien activée pour votre projet

### "Invalid JSON" ou erreur de parsing
- Vérifiez que le fichier service-account.json n'est pas corrompu
- Re-téléchargez la clé depuis Google Cloud Console si nécessaire

### Avantages du Service Account
- ✅ Pas d'interaction utilisateur requise (automatique)
- ✅ Idéal pour les scripts automatisés
- ✅ Pas de token qui expire
- ✅ Plus sécurisé pour les environnements de production