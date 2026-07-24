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

### Automatique (GitHub Pages)

Chaque `git push` sur `main` déclenche le workflow [.github/workflows/deploy.yml](.github/workflows/deploy.yml) qui construit et publie le site sur **https://lirei-lab.github.io/lireiweb/**.

### Manuel (serveur de l'UQTR ou autre)

Le site est entièrement statique : copiez le contenu de `dist/` sur n'importe quel serveur web (Apache, Nginx, serveur de l'UQTR…). Aucun environnement d'exécution n'est requis.

Si le site est servi sous un sous-chemin (par ex. `https://exemple.ca/lirei/`), construisez avec :

```bash
BASE_PATH=/lirei npm run build
```

## CMS (interface d'administration)

Le site intègre [Sveltia CMS](https://github.com/sveltia/sveltia-cms) : une interface visuelle à l'adresse `/admin/` pour modifier l'équipe, les publications, les projets et les actualités **sans toucher au code**.

### Mode local (approche retenue — aucune configuration)

Le contenu est maintenu localement, sans aucun serveur d'authentification :

1. `npm run dev`
2. Ouvrir `http://localhost:4321/admin/` (navigateur basé sur Chromium : Chrome, Edge).
3. Cliquer sur **« Work with Local Repository »** et sélectionner le dossier du projet.
4. Éditer avec les formulaires, puis `git commit` + `git push` : le site se reconstruit et se redéploie automatiquement.

C'est tout — pas d'OAuth, pas de service externe. La configuration des collections vit dans [public/admin/config.yml](public/admin/config.yml).

### Option — édition web par plusieurs personnes (facultatif)

Si, plus tard, plusieurs membres non techniques doivent éditer depuis leur navigateur en production, il faudra un petit relais OAuth (le secret GitHub ne peut pas vivre dans un site statique). Ce relais peut être hébergé n'importe où — un worker [sveltia-cms-auth](https://github.com/sveltia/sveltia-cms-auth) gratuit sur Cloudflare, une fonction serverless, ou le serveur de l'UQTR — puis renseigné via `base_url` dans `config.yml`. Non nécessaire pour le mode local ci-dessus.

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

> **Critère d'inclusion :** le catalogue ne recense que les publications dont **le professeur Kodjo Agbossou est coauteur** (au moins un auteur nommé « Agbossou »).

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
