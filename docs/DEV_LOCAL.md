# Lancer l'application en local (sans toucher à la production)

L'app peut tourner en local avec une **base SQLite** sur votre PC. La base de données du serveur de production **n'est jamais utilisée ni modifiée** quand vous travaillez en local.

## Prérequis

- Python 3 avec `venv` activé
- Dépendances installées : `pip install -r requirements.txt`

## Configuration en 3 étapes

### 1. Créer le fichier de config locale

À la racine du projet, copiez l'exemple :

```bash
copy .env.local.example .env.local
```

(sous Linux/Mac : `cp .env.local.example .env.local`)

Le fichier **`.env.local`** est déjà dans `.gitignore` : il ne sera **jamais envoyé** sur le serveur avec `git push`.  
(Si vous avez déjà un `.env.local`, assurez-vous qu’il contient `FLASK_ENV=development`, `FLASK_DEBUG=True` et `DATABASE_URL=` pour forcer SQLite.)

### 2. Initialiser la base SQLite locale (première fois)

Avec `.env.local` en place, l'app utilise SQLite (fichier `instance/app.db`). Créez les tables :

```bash
flask db upgrade
```

### 3. Lancer l'app

```bash
py run.py
```

Ouvrez http://localhost:5000 (ou le port indiqué).

## Pourquoi la production n'est pas touchée ?

- **En local** : la présence de `.env.local` fait que la config charge `FLASK_ENV=development` et `DATABASE_URL=` (vide), donc **SQLite** dans `instance/app.db`.
- **Sur le serveur** : il n'y a **pas** de `.env.local` (vous ne le déployez pas). Seul `.env` est utilisé, avec l’URL PostgreSQL de production. Vos `git push` n’envoient que le code ; la base de données du serveur reste celle configurée dans son `.env`.

En résumé : **local = SQLite locale**, **serveur = PostgreSQL de prod**. Les deux sont totalement séparés.
