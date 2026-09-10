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

Chaque `git push` sur `main` déclenche le workflow [.github/workflows/deploy.yml](.github/workflows/deploy.yml) qui construit et publie le site sur **https://lirei-lab.github.io/**.

### Manuel (serveur de l'UQTR ou autre)

Le site est entièrement statique : copiez le contenu de `dist/` sur n'importe quel serveur web (Apache, Nginx, serveur de l'UQTR…). Aucun environnement d'exécution n'est requis.

Si le site est servi sous un sous-chemin (par ex. `https://exemple.ca/lirei/`), construisez avec :

```bash
BASE_PATH=/lirei npm run build
```

## CMS (interface d'administration)

Le site intègre [Sveltia CMS](https://github.com/sveltia/sveltia-cms) : une interface visuelle à l'adresse `/admin/` pour modifier l'équipe, les publications, les projets et les actualités **sans toucher au code**.

Deux façons de se connecter, **aucune ne nécessite de serveur OAuth** :

### A. Jeton d'accès GitHub — recommandé (fonctionne depuis n'importe quel poste)

À privilégier si vous éditez depuis un poste **différent** de celui où vit le dépôt (par ex. navigateur sur Windows, code sur un serveur Linux en SSH) : cette méthode parle directement à GitHub, sans fichiers locaux.

1. Sur GitHub : **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**. Portée : dépôt `lirei-lab/lirei-lab.github.io`, permission **Contents : Read and write**. Copier le jeton.
2. Ouvrir `/admin/` — soit en production (**https://lirei-lab.github.io/admin/**, aucun `npm` requis), soit en local (`npm run dev` → `http://localhost:4321/admin/`).
3. Cliquer sur **« Sign In Using Access Token »** et coller le jeton.
4. Éditer avec les formulaires : chaque sauvegarde crée un commit sur GitHub, ce qui redéploie le site automatiquement.

### B. Dépôt local (« Work with Local Repository »)

Fonctionne uniquement quand **le navigateur et les fichiers du dépôt sont sur la même machine** (l'API navigateur d'accès aux fichiers ne peut pas atteindre un dossier distant en SSH). Sur ce poste :

1. `npm run dev`
2. Ouvrir `http://localhost:4321/admin/` (navigateur basé sur Chromium : Chrome, Edge).
3. Cliquer sur **« Work with Local Repository »** et sélectionner le dossier du projet.
4. Éditer, puis `git commit` + `git push`.

La configuration des collections vit dans [public/admin/config.yml](public/admin/config.yml).

### Option — connexion GitHub OAuth pour plusieurs éditeurs (facultatif)

Le bouton « Sign In with GitHub » (flux OAuth classique) exige un petit relais qui garde le secret GitHub (impossible dans un site statique). Ce relais peut être hébergé n'importe où — un worker [sveltia-cms-auth](https://github.com/sveltia/sveltia-cms-auth) gratuit sur Cloudflare, une fonction serverless, ou le serveur de l'UQTR — puis renseigné via `base_url` dans `config.yml`. Inutile pour les méthodes A et B ci-dessus.

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

### Mettre à jour les publications

Le catalogue se met à jour à partir de [Crossref](https://www.crossref.org/) (la
notice de l'éditeur : titre, auteurs, revue, DOI) et
d'[OpenAlex](https://openalex.org/) (qui retrouve des articles que la recherche
par nom de Crossref classe trop bas) :

```bash
python3 scripts/update-publications.py            # rapport : ce qui manque, rien n'est écrit
python3 scripts/update-publications.py --write    # ajoute les fiches et régénère la carte des sujets
python3 scripts/update-publications.py --scholar  # recoupe aussi avec le profil Google Scholar
python3 scripts/update-publications.py --since 2019   # remonte plus loin (défaut : l'année précédente)
```

Le script ne modifie jamais une fiche existante : une publication déjà présente
(même DOI ou même titre) est ignorée, donc les corrections faites à la main
sont conservées. Les prépublications (SSRN, Preprints.org) sont écartées ; la
version publiée les remplace. D'autres chercheurs s'appellent Agbossou : une
publication n'est retenue que si Crossref indique l'ORCID ou le prénom « Kodjo »,
ou l'initiale « K. » avec un coauteur connu de l'équipe ou des diplômés.

**Automatiquement, le 1er de chaque mois**, le workflow `.github/workflows/publications.yml`
lance le script et, s'il trouve du nouveau, ouvre une *pull request* « Nouvelles
publications à valider » avec la liste et les liens DOI. Relisez-la (type, année,
auteurs), corrigez au besoin dans la branche, puis fusionnez : le site se
redéploie. On peut aussi le déclencher à la main dans l'onglet **Actions**. Pour
que GitHub Actions ait le droit d'ouvrir la PR, activez une fois *Settings →
Actions → General → Allow GitHub Actions to create and approve pull requests*.

Google Scholar n'a pas d'API et bloque les serveurs : `--scholar` est donc à
lancer depuis un poste. Ce qui figure sur Scholar sans DOI retrouvable (brevets,
thèses) est seulement listé ; si Google affiche un captcha, enregistrez la page du
profil depuis le navigateur et passez-la avec `--scholar-file page.html`.

### Ajouter une publication à la main

Pour une publication sans DOI, créez `src/content/publications/2026-titre-court.json` :

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

#### Mettre à jour la carte des sujets

La carte interactive en haut de la page Publications est calculée hors ligne, à
partir des titres. Après avoir ajouté ou retiré des publications :

```bash
python3 scripts/build-topics.py            # régénère src/data/topics.json
python3 scripts/build-topics.py --audit    # contrôle : couverture et sujets orphelins
```

Le vocabulaire des sujets (leurs noms français et anglais, et les motifs qui les
reconnaissent dans un titre) est en tête de `scripts/build-topics.py`. L'audit
signale les publications qu'aucun sujet ne couvre : c'est le bon moment pour
élargir un motif ou ajouter un sujet. Le calcul est déterministe — mêmes
publications, même carte.

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
