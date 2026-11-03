# Книга рецептів

A simple recipe blog built with Flask. It has a custom admin panel, categories and tags, recipe photos, and search.

## Setup
```bash
.venv/bin/pip install -r requirements.txt
cp .env.example .env            # then set a real SECRET_KEY
.venv/bin/flask --app run init-db
.venv/bin/flask --app run create-admin
.venv/bin/flask --app run seed  # optional: adds sample recipes
.venv/bin/flask --app run run --debug
```
- Public site: http://127.0.0.1:5000
- Admin panel: http://127.0.0.1:5000/admin

The database is stored in `instance/recipes.db` and uploaded photos in `uploads/`.
