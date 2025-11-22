# Projet 2A 2025 — EnsaiGPT

---

##  Présentation rapide

**EnsaiGPT** est un projet Python conçu pour offrir une expérience de développement optimale et isolée, grâce à PDM.  
Le projet vise à résoudre les principaux problèmes rencontrés en data science comme :
- Plusieurs versions de Python coexistantes
- Sélection incohérente de l'interpréteur selon les outils
- Conflits de version liés aux paquets globaux

Chaque projet dispose ainsi de son propre environnement virtuel, assurant stabilité et reproductibilité.

---

##  Environnement de développement

- **Gestionnaire de paquets : [PDM](https://pdm.fming.dev/)**
  - Déclaration des dépendances via `pyproject.toml`
  - Versions verrouillées dans `pdm.lock`
  - Création automatique d’un environnement virtuel isolé
  - Configuration centralisée

- **Formatage & Linting : [Ruff](https://github.com/astral-sh/ruff)**
  - Formatage, linting et tri des imports ultra-rapide grâce à Rust
  - Remplace les classiques : `flake8`, `black`, `isort`

- **Vérification de types : [MyPy](http://mypy-lang.org/)**
  - Optionnelle mais vivement recommandée.
  - S’utilise via :  
    ```
    pdm typecheck
    ```

---

##  Comment utiliser le projet ?

1. **Installer PDM**
   ```bash
   pip install --user pdm
   ```

2. **Installer les dépendances**
   ```bash
   pdm install
   ```
   > Installe toutes les dépendances dans l’environnement virtuel isolé du projet.

3. **Configurer l’environnement**
   - Copier `.env.example` vers `.env`
   - Renseigner les accès BDD et API nécessaires

4. **Initialiser la base PostgreSQL**
   - Soit via le script SQL : `data/init_db.sql`
   - Soit via le script Python : `src/Database/init_db.py`

5. **Lancer l’application**
   ```bash
   pdm run python src/main.py
   ```

6. **Gérer les dépendances**
   - **Ajouter :**  
     ```bash
     pdm add nom-du-package
     ```
   - **Supprimer :**  
     ```bash
     pdm remove nom-du-package
     ```

7. **Outils qualité**
   - **Formatage :**  
     ```bash
     pdm format
     ```
   - **Lint :**  
     ```bash
     pdm lint
     ```
   - **Correction auto :**  
     ```bash
     pdm lint --fix
     ```
   - **Type checking :**  
     ```bash
     pdm typecheck
     ```

---

##  Structure du projet

_(Structure identique, affichage inchangé)_

---

##  Fonctionnalités principales

- Gestion des utilisateurs
- Création & gestion des conversations
- Collaboration multi-utilisateur
- Système de messagerie
- Intégration LLM externe
- Statistiques
- Export TXT
- Gestion des feedbacks
- Fonctionnalités de recherche
- CLI interactive
- Support PostgreSQL
- Tests unitaires + d’intégration

---

## � Packaging

Le projet **n’est pas destiné à la distribution** (`distribution = false`).  
Téléchargez-le via l’option **Download ZIP** sur GitHub.

---

##  Pour la notation

```bash
pdm install
pdm run python src/main.py
```

---

##  Librairies recommandées

- `requests`
- `FastAPI`, `Uvicorn`
- `psycopg2`
- `pytest`

---

##  Extensions VSCode recommandées

La liste complète est dans `extensions.txt`.  
Pensez à **désactiver les linters doublons** (`flake8`, `pylance`, ...).

---
