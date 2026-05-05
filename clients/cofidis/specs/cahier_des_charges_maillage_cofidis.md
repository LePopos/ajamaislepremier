# Maillage interne Cofidis — Règles par type de page

**Objectif** : sur chaque page de contenu, insérer des liens internes organisés en blocs. Ce document dit quels blocs mettre, combien de liens, et comment les sélectionner.

---

## Les 4 blocs disponibles

| Bloc | Nom affiché (exemple) | Contenu |
|---|---|---|
| **BLOC Q&A** | "Questions fréquentes sur le même sujet" | Pages Q&A du même thème |
| **BLOC GUIDE** | "Besoin d'autres conseils sur le même thème ?" | Pages guides du même thème |
| **BLOC INCONTOURNABLES** | "À voir aussi" | 6 pages fixes (simulateurs, pages produit clés) |
| **BLOC OUTIL** | "Estimez votre projet" | Simulateur(s) du même thème |

---

## Règle d'activation par type de page

| Type de page | BLOC Q&A | BLOC GUIDE | BLOC INCONTOURNABLES | BLOC OUTIL |
|---|:---:|:---:|:---:|:---:|
| **Page Q&A** | ✅ 5 liens | ✅ 6 liens | ✅ 6 liens | ✅ 2 liens |
| **Page Guide** | ✅ 5 liens | ✅ 6 liens | ✅ 6 liens | ✅ 2 liens |
| **Page Produit** | ✅ 5 liens | ✅ 6 liens | ✅ 6 liens | ✅ 2 liens |
| **Page Hub** | — | ✅ 6 liens | ✅ 6 liens | ✅ 2 liens |
| **Outil / Simulateur** | — | — | ✅ 6 liens | — |
| **Lexique** | — | — | ✅ 6 liens | — |

---

## Comment sélectionner les liens de chaque bloc

### BLOC Q&A — *5 liens*
→ Prendre les pages Q&A **du même thème** (ex : toutes les Q&A "crédit cuisine")
→ Exclure la page en cours

### BLOC GUIDE — *6 liens*
→ Prendre les pages Guide **du même thème**
→ Si moins de 4 guides disponibles dans le thème : compléter avec des guides de **thèmes proches** (voir tableau ci-dessous)
→ Exclure la page en cours

### BLOC INCONTOURNABLES — *6 liens fixes*
Ces 6 pages apparaissent sur **toutes les pages**, sans exception :
1. `/fr/credit/simulation-credit.html`
2. `/fr/credit.html`
3. `/fr/pret-personnel/pret-sur-mesure.html`
4. `/fr/pret-personnel/simulation-pret.html`
5. `/fr/credit/credit-renouvelable.html`
6. `/fr/credit/credit-consommation.html`

### BLOC OUTIL — *2 liens*
→ Prendre le ou les simulateurs **du même thème**
→ Si aucun simulateur thématique : utiliser `/fr/pret-personnel/simulation-pret.html` par défaut

---

## Organisation par thème (IDs)

Chaque page appartient à un thème. Le thème est déterminé par l'URL.

| Thème | Pages concernées (début d'URL) |
|---|---|
| Rénovation énergétique | `/fr/pret-renovation-energetique/` |
| Travaux | `/fr/pret-personnel/pret-travaux/` |
| Crédit cuisine | `/fr/pret-personnel/credit-cuisine/` |
| Crédit auto | `/fr/pret-personnel/credit-auto/` ou `/fr/credit-auto/` |
| Crédit moto | `/fr/pret-personnel/credit-moto-scooter/` |
| Crédit salle de bain | `/fr/pret-personnel/credit-salle-de-bain/` |
| Crédit déco | `/fr/pret-personnel/credit-decoration/` |
| Crédit piscine | `/fr/pret-personnel/credit-piscine/` |
| Crédit mariage | `/fr/pret-personnel/credit-mariage/` |
| Crédit voyage | `/fr/pret-personnel/credit-voyage/` |
| Prêt personnel (générique) | `/fr/pret-personnel/` (autres) |
| Crédit général | `/fr/credit/`, `/fr/guide-credit/` |
| Rachat de crédit | `/fr/rachat-de-credit/` |

**Thèmes proches** (pour compléter le BLOC GUIDE si besoin) :

| Thème | Thèmes proches |
|---|---|
| Rénovation énergétique | Travaux, Crédit général |
| Travaux | Rénovation énergétique, Crédit cuisine, Crédit SDB |
| Crédit cuisine | Travaux, Crédit déco |
| Crédit auto | Crédit moto |
| Crédit moto | Crédit auto |
| Prêt personnel | Crédit général |
| Crédit général | Prêt personnel, Rachat de crédit |

---

## Livrable associé

Un fichier Excel `cofidis_maillage_mapping.xlsx` sera généré automatiquement avec :
- **Onglet Mapping** : pour chaque page, les URLs de chaque bloc déjà renseignées et prêtes à intégrer
- **Onglet Inventaire** : toutes les URLs du site classées par type et par thème
