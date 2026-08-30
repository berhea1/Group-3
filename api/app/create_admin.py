import argparse
import getpass
import os

import psycopg
from passlib.context import CryptContext


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or reset a Shop System administrator")
    parser.add_argument("username")
    parser.add_argument("--name", required=True)
    parser.add_argument("--barcode", required=True)
    args = parser.parse_args()

    password = getpass.getpass("Admin password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        raise SystemExit("Passwords do not match")
    if len(password) < 12:
        raise SystemExit("Use a password at least 12 characters long")

    database_url = os.environ["DATABASE_URL"]
    password_hash = CryptContext(schemes=["bcrypt"], deprecated="auto").hash(password)

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (role, full_name, barcode_value)
                VALUES ('admin', %s, %s)
                ON CONFLICT (barcode_value) DO UPDATE
                  SET role='admin', full_name=EXCLUDED.full_name, is_active=TRUE, updated_at=NOW()
                RETURNING id
                """,
                (args.name, args.barcode),
            )
            user_id = cur.fetchone()[0]
            cur.execute(
                """
                INSERT INTO admin_accounts (username, password_hash, user_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (username) DO UPDATE
                  SET password_hash=EXCLUDED.password_hash, user_id=EXCLUDED.user_id, is_active=TRUE
                """,
                (args.username, password_hash, user_id),
            )
    print(f"Administrator '{args.username}' is ready.")


if __name__ == "__main__":
    main()

