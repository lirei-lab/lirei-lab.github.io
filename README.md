# Site web du LIREI / LIREI Website

Site web bilingue (français / anglais) du **Laboratoire d'innovation et de recherche en énergie intelligente (LIREI)** de l'Université du Québec à Trois-Rivières, membre de l'Institut de recherche sur l'hydrogène (IRH).

Site statique construit avec [Astro](https://astro.build) : le français est servi à la racine (`/`) et l'anglais sous `/en/`.

## Prérequis

- Node.js ≥ 20 (Astro 5)

## Commandes

```bash
npm install        # installer les dépendances
npm run dev        # serveur de développement (http://localhost:4321)
npm run build      # génère le site statique dans dist/
npm run preview    # prévisualise le contenu de dist/
```

## Déploiement

Le site est entièrement statique : copiez le contenu de `dist/` sur n'importe quel serveur web (Apache, Nginx, serveur de l'UQTR…). Aucun environnement d'exécution n'est requis.

Si le site est servi sous un sous-chemin (par ex. `https://exemple.ca/lirei/`), construisez avec :

```bash
BASE_PATH=/lirei npm run build
```

## Gérer le contenu

Tout le contenu structuré vit dans `src/content/`. Ajouter du contenu = ajouter un fichier ; le schéma est validé automatiquement au `build`.

### Ajouter un membre de l'équipe

Créez `src/content/team/prenom-nom.json` :

```json
{
  "name": "Prénom Nom",
  "category": "student",
  "role": { "fr": "Étudiant(e) aux cycles supérieurs", "en": "Graduate Student" },
  "topic": { "fr": "Sujet de recherche", "en": "Research topic" },
  "email": "prenom.nom@uqtr.ca",
  "order": 60
}
```

`category` : `direction`, `professor`, `staff`, `postdoc` ou `student`. `order` contrôle l'ordre d'affichage dans chaque groupe.

### Ajouter une publication

Créez `src/content/publications/2026-titre-court.json` :

```json
{
  "title": "Titre de l'article",
  "authors": ["N. Henao", "K. Agbossou"],
  "venue": "IEEE Transactions on Smart Grid",
  "year": 2026,
  "type": "journal",
  "doi": "10.1109/XXX.2026.XXXXXXX"
}
```

`type` : `journal`, `conference` ou `other`. `doi` et `venue` sont optionnels.

### Ajouter un projet

Créez `src/content/projects/mon-projet.md` :

```md
---
title:
  fr: "Titre du projet"
  en: "Project title"
summary:
  fr: "Résumé en une ou deux phrases."
  en: "One- or two-sentence summary."
axis: smartgrids
status: active
partners: ["Hydro-Québec"]
---
```

`axis` : `smartgrids`, `residential`, `ml`, `hydrogen`, `flexibility` ou `ev`. `status` : `active` ou `completed`.

### Modifier les textes des pages

Tous les textes d'interface et de contenu éditorial sont dans `src/i18n/fr.json` et `src/i18n/en.json`. Modifiez les deux fichiers pour garder les langues synchronisées.

## Structure

```
src/
├── i18n/            # dictionnaires FR/EN + aide de routage
├── layouts/         # gabarit de base (en-tête, pied de page, SEO)
├── components/      # composants réutilisables et pages partagées
├── content/         # équipe, publications, projets (collections typées)
├── pages/           # routes FR à la racine, routes EN sous en/
└── styles/          # feuille de style globale
```
