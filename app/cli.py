"""Commandes d'administration : `uv run python -m app.cli create-admin EMAIL`."""

import argparse
import asyncio
import getpass
import sys

from sqlalchemy import select

from app.db import SessionLocal, engine
from app.models import User
from app.security import hash_password


async def create_admin(email: str, password: str) -> str:
    email = email.lower()
    async with SessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == email))
        if user is None:
            db.add(User(email=email, hashed_password=hash_password(password), is_admin=True))
            result = "créé"
        else:
            user.is_admin = True
            user.hashed_password = hash_password(password)
            result = "promu admin (mot de passe mis à jour)"
        await db.commit()
    await engine.dispose()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create-admin", help="Crée ou promeut un administrateur")
    create.add_argument("email")
    args = parser.parse_args()

    password = getpass.getpass("Mot de passe : ")
    if len(password) < 8:
        sys.exit("Le mot de passe doit faire au moins 8 caractères.")
    if password != getpass.getpass("Confirmer : "):
        sys.exit("Les mots de passe ne correspondent pas.")
    print(f"Admin {args.email} {asyncio.run(create_admin(args.email, password))}.")


if __name__ == "__main__":
    main()
