# Fridge — back end

API (FastAPI + PostgreSQL) pour suivre les produits mis au frigo et repérer ceux qui vont périmer.

## Démarrage

Prérequis : [mise](https://mise.jdx.dev) et Docker.

```sh
mise install          # Python 3.12, uv, prek aux versions épinglées
cp .env.example .env  # puis changer SECRET_KEY
mise run install      # dépendances + hooks git (prek)
mise run db           # PostgreSQL (crée aussi la base fridge_test)
mise run migrate      # migrations Alembic
mise run dev          # API sur http://localhost:8000 (Swagger : /docs)
```

Tâches utiles : `mise run test`, `mise run lint`, `prek run --all-files`.

> La base `fridge_test` n'est créée qu'à la première initialisation du volume Postgres.
> Sur un volume existant : `docker compose exec db createdb -U fridge fridge_test`.

## Vue admin

Interface web ([SQLAdmin](https://aminalaee.dev/sqladmin/)) sur http://localhost:8000/admin : gestion des utilisateurs (recherche, passage admin, suppression) et des produits (recherche, filtres, édition).

Seuls les comptes avec `is_admin = true` peuvent s'y connecter (l'accès est revalidé à chaque requête). Créer le premier admin :

```sh
mise run create-admin ton@email.com   # demande le mot de passe ; crée ou promeut le compte
```

## Endpoints (`/api/v1`)

| Méthode | Route | Rôle |
|---|---|---|
| POST | `/auth/register` | Création de compte |
| POST | `/auth/login` | JWT (formulaire OAuth2 : `username` = email) |
| GET | `/auth/me` | Utilisateur courant |
| POST | `/products` | Ajouter un produit |
| GET | `/products` | Lister (`consumed`, `category`, `limit`, `offset`) |
| GET | `/products/expiring?days=3` | Non consommés expirant dans N jours (périmés inclus) |
| GET/PATCH/DELETE | `/products/{id}` | Détail / modifier / supprimer |
| GET | `/health` | Santé de l'API |

Chaque produit expose `days_left` (négatif si périmé) et `expired`. Les produits sont isolés par utilisateur.
