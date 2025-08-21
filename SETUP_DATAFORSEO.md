# Configuration du Suivi SEO Data for SEO

## 🚀 Installation

1. **Installer les dépendances**:
```bash
pip install -r requirements_dataforseo.txt
```

2. **Lancer le script une première fois** pour créer le fichier de configuration :
```bash
python3 dataforseo_tracker.py
```

3. **Configurer le fichier `dataforseo_config.json`** qui sera créé automatiquement

## ⚙️ Configuration

### 1. API Data for SEO
```json
"api": {
    "login": "your_dataforseo_login",
    "password": "your_dataforseo_password"
}
```

### 2. Mots-clés et domaine à suivre
```json
"tracking": {
    "domain": "example.com",
    "keywords": [
        "mot-clé principal",
        "terme de recherche 2",
        "expression longue traîne"
    ],
    "location_code": 2250,  // France
    "language_code": "fr",
    "device": "desktop"     // desktop, mobile, tablet
}
```

### 3. Configuration email
```json
"email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "votre-email@gmail.com",
    "sender_password": "mot-de-passe-application",
    "recipients": [
        "destinataire1@example.com",
        "destinataire2@example.com"
    ]
}
```

**Note Gmail** : Utilisez un mot de passe d'application, pas votre mot de passe habituel.

### 4. Rapports
```json
"reports": {
    "csv_export": true,
    "csv_filename": "positions_report_{date}.csv",
    "history_days": 30
}
```

## 🧪 Test

Testez avec seulement 3 mots-clés :
```bash
python3 dataforseo_tracker.py --test
```

## ⏰ Automatisation

### Configuration du cron quotidien
```bash
chmod +x cron_setup.sh
./cron_setup.sh
```

### Configuration manuelle
```bash
crontab -e
```

Ajouter la ligne (exemple pour 9h00 chaque jour) :
```
0 9 * * * /usr/bin/python3 /chemin/vers/dataforseo_tracker.py >> /chemin/vers/logs/seo_tracking.log 2>&1
```

## 📊 Fonctionnalités

- **Suivi de positions** : Top 100 des résultats Google
- **Métriques** : Position, volume de recherche, CPC, concurrence  
- **Localisation** : Paramétrable par pays/région
- **Device** : Desktop, mobile ou tablette
- **Rapports** : HTML par email + export CSV
- **Historique** : Sauvegarde des données dans des fichiers CSV horodatés

## 📈 Rapport Email

Le rapport inclut :
- **Statistiques générales** : Nombre de mots-clés suivis, classés, position moyenne
- **Top 10** : Meilleures positions avec URLs
- **Non classés** : Mots-clés hors top 100
- **Pièce jointe CSV** : Données détaillées

## 🔍 Surveillance

Vérifier les logs :
```bash
tail -f logs/seo_tracking.log
```

Vérifier les tâches cron :
```bash
crontab -l
```

## 🛠️ Dépannage

### Erreurs communes
- **Authentification** : Vérifiez login/password Data for SEO
- **Email** : Utilisez un mot de passe d'application Gmail
- **Quota API** : Data for SEO limite les requêtes par mois
- **Permissions** : Assurez-vous que le script est exécutable

### Codes de localisation courants
- France : `2250`
- États-Unis : `2840`
- Royaume-Uni : `2826`
- Canada : `2124`

### Support API Data for SEO
- Documentation : https://docs.dataforseo.com/
- Limits : https://dataforseo.com/apis/pricing

## 📋 Exemple de sortie

```
🚀 Démarrage du suivi quotidien - 2024-01-15 09:00:00
==============================================================
Début du suivi pour 50 mots-clés...
Domaine: example.com
------------------------------------------------------------
[1/50] Traitement de 'assurance auto'...
  ✅ Position 15 - https://example.com/assurance-auto
[2/50] Traitement de 'crédit immobilier'...
  ❌ Non classé (>100)
...

📊 Résumé: 50 mots-clés traités
   - 35 classés dans le top 100
   - 15 non classés

📄 Export CSV: positions_report_20240115.csv
📧 Envoi du rapport par email...
✅ Email envoyé à 2 destinataire(s)

✅ Suivi quotidien terminé avec succès!
```