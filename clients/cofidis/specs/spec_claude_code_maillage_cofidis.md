# Spec — Maillage interne Cofidis : mapping des pages réelles

## Objectif

Générer un fichier Excel (`cofidis_maillage_mapping.xlsx`) qui liste, pour chaque page de contenu Cofidis (Q&A et Guide en priorité), les 4 blocs de maillage à appliquer avec les URLs réelles à appeler.

---

## Étape 1 — Récupérer le plan du site

Fetch le sitemap Cofidis pour extraire toutes les URLs :

```
https://www.cofidis.fr/sitemap.xml
```

Si le sitemap est un sitemap index, itérer sur tous les sitemaps enfants. Extraire toutes les URLs `<loc>` dans une liste.

---

## Étape 2 — Classifier chaque URL par type de page

Pour chaque URL, appliquer les règles de classification suivantes **sur la base du pattern URL** (pas besoin de fetcher chaque page) :

| Type | Règle URL |
|---|---|
| `HUB` | URL de profondeur 1 sans extension, ou contenant `guide-` | ex: `/fr/pret-renovation-energetique.html`, `/fr/guide-credit.html` |
| `PRODUIT` | URL de profondeur 2 sans sous-dossier de contenu éditorial | ex: `/fr/pret-personnel/credit-cuisine.html` |
| `GUIDE` | URL de profondeur 3+ dont le dernier segment ne ressemble pas à une question | ex: `/fr/pret-personnel/pret-travaux/meilleur-systeme-chauffage.html` |
| `Q&A` | URL de profondeur 2 dont le dernier segment ressemble à une question ou contient des mots-clés Q&A (liste ci-dessous) | ex: `/fr/pret-renovation-energetique/audit-energetique-obtenir-credit.html` |
| `OUTIL` | URL contenant `simulation`, `simulateur`, `calculette`, `calculatrice` | ex: `/fr/pret-personnel/simulation-pret.html` |
| `LEXIQUE` | URL contenant `lexique` | ex: `/fr/lexique-credit.html` |
| `AUTRE` | Tout le reste (institutionnel, espace client, assurance, rachat…) — exclure du mapping |

**Mots-clés Q&A** (présence dans le slug = Q&A) :
`comment`, `pourquoi`, `quand`, `quel`, `quelle`, `quels`, `peut-on`, `faut-il`, `combien`, `est-ce`, `quoi`, `qui`, `obtenir`, `demander`, `savoir`

**Pages à exclure du mapping** (ne pas traiter) :
- `/fr/espace-client/`
- `/fr/aide-et-contact/`
- `/fr/decouvrir-cofidis/`
- `/fr/infos_legales`
- `/fr/gestion-donnees`
- `/fr/accessibilite/`
- `/fr/index.html`
- Toute URL contenant `.cgi`, `.aspx`, `#`

---

## Étape 3 — Assigner un ID thématique à chaque URL

L'ID thématique est dérivé du **premier segment de path après `/fr/`** (le silo URL).

Mapping silo → ID :

```python
SILO_TO_ID = {
    "pret-renovation-energetique": "id_renovation_energetique",
    "pret-personnel/pret-travaux": "id_travaux",          # priorité sur pret-personnel
    "pret-personnel/credit-cuisine": "id_credit_cuisine",
    "pret-personnel/credit-auto": "id_credit_auto",
    "pret-personnel/credit-moto-scooter": "id_credit_moto",
    "pret-personnel/credit-salle-de-bain": "id_credit_sdb",
    "pret-personnel/credit-decoration": "id_credit_deco",
    "pret-personnel/credit-piscine": "id_credit_piscine",
    "pret-personnel/credit-veranda": "id_credit_veranda",
    "pret-personnel/credit-mariage": "id_credit_mariage",
    "pret-personnel/credit-voyage": "id_credit_voyage",
    "pret-personnel/credit-camping-car": "id_credit_campingcar",
    "pret-personnel/credit-demenagement": "id_credit_demenagement",
    "pret-personnel": "id_pret_personnel",                # fallback silo pret-personnel
    "credit-velo": "id_credit_velo",
    "credit-auto": "id_credit_auto",
    "rachat-de-credit": "id_rachat_credit",
    "assurance": "id_assurance",
    "credit": "id_credit_general",
    "paiement-a-credit": "id_credit_general",
    "guide-credit": "id_credit_general",
    "guide-projets": "id_projets_general",
    "lexique-credit": "id_lexique",
    "tous-vos-projets": "id_projets_general",
}
```

**Règle** : parcourir les clés du plus spécifique au moins spécifique. La première correspondance gagne.

---

## Étape 4 — Définir les pages incontournables (BLOC-INCONTOURNABLES)

Ces 6 URLs sont fixes pour toutes les pages :

```python
INCONTOURNABLES = [
    "https://www.cofidis.fr/fr/credit/simulation-credit.html",
    "https://www.cofidis.fr/fr/credit.html",
    "https://www.cofidis.fr/fr/pret-personnel/pret-sur-mesure.html",
    "https://www.cofidis.fr/fr/pret-personnel/simulation-pret.html",
    "https://www.cofidis.fr/fr/credit/credit-renouvelable.html",
    "https://www.cofidis.fr/fr/credit/credit-consommation.html",
]
```

---

## Étape 5 — Construire le mapping par page

Pour chaque page de type `Q&A`, `GUIDE`, `PRODUIT`, `HUB` (dans cet ordre de priorité) :

### BLOC-QA
- Prendre toutes les pages de type `Q&A` ayant le **même ID thématique**
- Exclure la page elle-même
- Trier par proximité de slug (Levenshtein ou simple tri alphabétique)
- Garder les **5 premières**

### BLOC-GUIDE
- Prendre toutes les pages de type `GUIDE` ayant le **même ID thématique**
- Exclure la page elle-même
- Compléter si < 4 résultats avec des `GUIDE` d'IDs sémantiquement proches (voir mapping ci-dessous)
- Garder les **6 premières**

**IDs proches** (pour complétion BLOC-GUIDE) :
```python
ID_PROCHES = {
    "id_renovation_energetique": ["id_travaux", "id_credit_general"],
    "id_travaux": ["id_renovation_energetique", "id_credit_cuisine", "id_credit_sdb"],
    "id_credit_cuisine": ["id_travaux", "id_credit_deco"],
    "id_credit_auto": ["id_credit_moto", "id_credit_velo"],
    "id_credit_moto": ["id_credit_auto", "id_credit_velo"],
    "id_pret_personnel": ["id_credit_general"],
    "id_credit_general": ["id_pret_personnel", "id_rachat_credit"],
    "id_rachat_credit": ["id_credit_general"],
    "id_assurance": ["id_credit_general"],
}
```

### BLOC-INCONTOURNABLES
- Toujours les 6 URLs fixes définies en Étape 4

### BLOC-OUTIL
- Prendre toutes les pages de type `OUTIL` ayant le **même ID thématique**
- Si aucune : prendre `/fr/pret-personnel/simulation-pret.html` par défaut
- Garder les **2 premières**
- Ne pas activer ce bloc pour les types `OUTIL` et `LEXIQUE`

---

## Étape 6 — Générer le fichier Excel

Créer un fichier `cofidis_maillage_mapping.xlsx` avec **2 onglets** :

### Onglet 1 : `Mapping`

Une ligne par page traitée, colonnes :

| Colonne | Description |
|---|---|
| `url_page` | URL complète de la page |
| `type_page` | HUB / PRODUIT / GUIDE / Q&A / OUTIL / LEXIQUE |
| `id_thematique` | ex: `id_renovation_energetique` |
| `bloc_qa_1` à `bloc_qa_5` | URLs du BLOC-QA |
| `bloc_guide_1` à `bloc_guide_6` | URLs du BLOC-GUIDE |
| `bloc_incontournables_1` à `bloc_incontournables_6` | URLs fixes |
| `bloc_outil_1` à `bloc_outil_2` | URLs BLOC-OUTIL |
| `nb_qa_dispo` | Nombre de Q&A disponibles dans le silo (info utile) |
| `nb_guide_dispo` | Nombre de guides disponibles dans le silo |

### Onglet 2 : `Inventaire`

Une ligne par URL récupérée dans le sitemap, colonnes :

| Colonne | Description |
|---|---|
| `url` | URL complète |
| `type_page` | Type classifié |
| `id_thematique` | ID assigné |
| `inclus_mapping` | OUI / NON (si la page est dans l'onglet Mapping) |

---

## Contraintes techniques

- Utiliser `requests` + `xml.etree.ElementTree` pour parser le sitemap
- Utiliser `openpyxl` pour générer l'Excel
- Ne pas fetcher les pages individuelles (classification uniquement par URL)
- Gérer les redirections (suivre les 301/302 au niveau sitemap si besoin)
- Timeout de 10s sur les requêtes HTTP
- Si le sitemap retourne une erreur, essayer `/fr/sitemap.xml` en fallback

---

## Livrable attendu

```
cofidis_maillage_mapping.xlsx
```

Avec un print en fin de script :
- Nombre total d'URLs récupérées
- Nombre par type (HUB, PRODUIT, GUIDE, Q&A, OUTIL, LEXIQUE, AUTRE)
- Nombre de pages dans l'onglet Mapping
