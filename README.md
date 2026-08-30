# Group 3 Shop System

Shared senior-design project for the machine-shop access system.

## What is included

- FastAPI web application and administrator interface
- PostgreSQL database with an initial schema
- Docker Compose deployment for Portainer
- Health checks and persistent database storage
- Isolated branch preview environments for each teammate

## Team workflow

Do not develop directly on `main`. Each teammate works on their preview branch, pushes changes, checks the matching preview website, and opens a pull request into `main` when the work is ready.

```text
personal preview branch -> personal preview website -> pull request -> main -> shop.riche10.com
```

| Person | GitHub username | Branch | Preview port | Preview address |
|---|---|---|---:|---|
| Abel | `berhea1` | `preview/berhea1` | 8101 | `berhea1.riche10.com` |
| Omari | `riche10` | `preview/riche10` | 8102 | `omari.riche10.com` |
| Mingchuan | `M-ming519` | `preview/m-ming519` | 8103 | `m-ming519.riche10.com` |
| Devin | `NDPDA` | `preview/ndpda` | 8104 | `ndpda.riche10.com` |
| Kyle | `KyleBurnsSchool` | `preview/kyleburnsschool` | 8105 | `kyleburnsschool.riche10.com` |
| David | `davidpenrose` | `preview/davidpenrose` | 8106 | `davidpenrose.riche10.com` |
| John | `jdjohnc1521` | `preview/jdjohnc1521` | 8107 | `jdjohnc1521.riche10.com` |

## Portainer deployment

Deploy from this repository with `docker-compose.yml`. The production stack watches `refs/heads/main` and uses port `8000`. Each preview stack watches its corresponding `refs/heads/preview/<username>` branch and uses the port in the table above.

Configure these values in each Portainer stack; do not commit real secrets:

```text
POSTGRES_DB=shopdb
POSTGRES_USER=app
POSTGRES_PASSWORD=<unique-random-password>
DATABASE_URL=postgresql://app:<same-password>@postgres:5432/shopdb
SESSION_SECRET=<unique-64-character-random-secret>
SESSION_COOKIE_NAME=<unique-preview-name>
SESSION_HTTPS_ONLY=true
SHOP_BIND_ADDRESS=192.168.10.65
SHOP_PORT=<port-from-table>
```

Every Portainer stack receives its own PostgreSQL volume, network, and containers. A preview stack cannot change the production database.

## Administrator setup

From the Portainer console for the desired stack's API container:

```text
python -m app.create_admin tkell --name "TKell" --barcode "ADMIN-001"
```

The command securely prompts for a password of at least 12 characters.
