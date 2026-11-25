# Template – minimal fullstack-mall

En liten utgångspunkt att bygga vidare på: ett React-frontend, ett FastAPI-backend med Swagger-dokumentation och en PostgreSQL-databas med stöd för vektorer (pgvector). Allt startas med Docker Compose.

## Snabbstart

Kräver Docker med Compose.

```bash
cp .env.example .env        # valfritt, standardvärden finns i docker-compose.yml
docker compose up --build   # bygger och startar alla tjänster
```

| Vad | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Swagger UI | http://localhost:8000/docs (även http://localhost:3000/docs) |
| ReDoc | http://localhost:8000/redoc |
| Databas | `localhost:5432`, användare/lösenord/databas `app` |

```bash
docker compose down         # stoppar, databasen finns kvar
docker compose down -v      # stoppar och raderar databasvolymen
```

## Containrarna

| Tjänst | Image / bygge | Port (värd → container) | Ansvar |
|---|---|---|---|
| `frontend` | `code/frontend/Dockerfile` (Node 24 → nginx) | 3000 → 80 | Serverar React-appen och vidarebefordrar `/api` och `/docs` till backend |
| `backend` | `code/backend/Dockerfile` (Python 3.14) | 8000 → 8000 | REST-API med FastAPI och Uvicorn |
| `db` | `pgvector/pgvector:pg17` | 5432 → 5432 | PostgreSQL 17 med tillägget `vector` |

Tjänsterna når varandra via sina namn på Compose-nätverket (t.ex. `db:5432` och `backend:8000`). `backend` startar först när databasens healthcheck (`pg_isready`) är grön.

### frontend

- Koden ligger i `code/frontend/`: `src/App.jsx` är startsidan, `src/components/` har en komponent per resurs (t.ex. `Items.jsx`), `src/api.js` har fetch-hjälpare och `src/main.jsx` monterar appen.
- Dockerfilen bygger i två steg. Först kör `node:24-alpine` `npm ci` och `npm run build` (Vite). Sedan kopieras det statiska resultatet i `dist/` till `nginx:alpine`.
- `nginx.conf` skickar `/api/`, `/docs`, `/redoc` och `/openapi.json` vidare till `backend:8000`. Övriga sökvägar faller tillbaka på `index.html`, så att klientroutning fungerar.
- Startsidan visar backend-status, listar items och har ett formulär för att lägga till nya.
- **Lokal utveckling med hot reload:** kör `npm install` och `npm run dev` i `code/frontend/`. Vite proxar `/api` till `localhost:8000`, så backend och db kan köras i Docker under tiden (`docker compose up db backend`).

### backend

- Koden ligger i `code/backend/app/`:
  - `main.py`: appen, `/api/health` och registrering av routers
  - `routers/items.py`: endpoints för items (en fil per resurs)
  - `routers/auth.py`, `routers/users.py`, `routers/config.py`: inloggning, användarhantering och växlar (se "Inloggning och användare")
  - `settings.py`, `features.py`, `security.py`, `auth.py`: inställningar från env, växlar, lösenordshashning och Bearer-skydd
  - `db.py`: anslutning, session och uppstart av schemat
  - `models.py`: SQLAlchemy-modeller
  - `schemas.py`: Pydantic-modeller, som också syns i Swagger
- Swagger UI finns på `/docs` och ReDoc på `/redoc`. Båda genereras automatiskt från endpoints och scheman.
- Vid start körs `CREATE EXTENSION IF NOT EXISTS vector` och tabeller skapas med `Base.metadata.create_all`. Någon migrering finns inte än (se "Bygga vidare").
- Endpoints:

  | Metod | Sökväg | Beskrivning |
  |---|---|---|
  | GET | `/api/health` | Hälsokontroll, `{"status": "ok"}` |
  | GET | `/api/items` | Lista alla items |
  | POST | `/api/items` | Skapa ett item (`name`, valfri `description` och `embedding`) |
  | POST | `/api/items/search` | De närmaste items till en vektor, sorterade på cosinusavstånd |
  | GET | `/api/config` | Miljö och växlar (alltid öppen) |
  | PUT | `/api/config` | Slå på eller av växlarna. Bara när `APP_ENV` är `local` eller `test`, annars 404 |
  | POST | `/api/auth/login` | Logga in med `email` och `password` och få en token |
  | POST | `/api/auth/logout` | Avsluta sessionen |
  | GET | `/api/auth/me` | Den inloggade användaren |
  | GET, POST | `/api/users` | Lista och skapa användare (admin) |
  | DELETE | `/api/users/{id}` | Ta bort en användare (admin). Root-admin och den egna användaren kan inte tas bort |

  Items-endpoints kräver `Authorization: Bearer <token>` när inloggning är påslagen.

- Beroenden finns i `requirements.txt`. Testberoenden finns i `requirements-dev.txt`.

### db

- Imagen är vanlig PostgreSQL 17 med tillägget pgvector förinstallerat.
- Datan sparas i volymen `pgdata` och finns kvar mellan omstarter.
- Tabellen `items` har kolumnen `embedding vector(EMBEDDING_DIM)`. Den får vara tom.
  - Längden sätts med `EMBEDDING_DIM` (standard 3, så att det är enkelt att testa i Swagger).
  - En embedding-modell ger oftast 384–1536 värden.
  - Byter du längd på en befintlig databas måste tabellen skapas om, till exempel med `docker compose down -v`.
- Vektorer med fel längd och nollvektorer avvisas med 422. Cosinusavstånd är inte definierat för en nollvektor.
- Exempel i Swagger: skapa items med `"embedding": [1, 0.1, 0]` och `[0, 1, 0]`. Sök sedan med `{"embedding": [1, 0, 0]}`.

## Miljövariabler

Läses från `.env` i roten (se `.env.example`). Alla har standardvärden.

| Variabel | Standard | Används till |
|---|---|---|
| `POSTGRES_USER` | `app` | Databasanvändare |
| `POSTGRES_PASSWORD` | `app` | Databaslösenord. Byt utanför lokal utveckling |
| `POSTGRES_DB` | `app` | Databasnamn |
| `EMBEDDING_DIM` | `3` | Längd på vektorn i `items.embedding` |
| `DB_PORT` | `5432` | Port på värden för databasen |
| `BACKEND_PORT` | `8000` | Port på värden för backend |
| `FRONTEND_PORT` | `3000` | Port på värden för frontend |
| `APP_ENV` | `local` | `local`, `test`, `staging` eller `production`. Config-sidan finns bara i `local` och `test` |
| `AUTH_ENABLED` | `false` | Inloggning och sessioner. I `local`/`test` kan config-sidan ändra den |
| `USER_MANAGEMENT_ENABLED` | `false` | Användarhantering. Kräver inloggning |
| `SESSION_TTL_MINUTES` | `60` | Hur länge en token gäller |
| `ADMIN_EMAIL` | `admin@example.com` | Root-admin, skapas eller uppdateras när backend startar |
| `ADMIN_PASSWORD` | tomt | Root-admins lösenord. Tomt betyder att ingen root-admin skapas |

Backend läser `DATABASE_URL`, som Compose bygger ihop från variablerna ovan.

## Inloggning och användare

Två valbara funktioner, båda avslagna från början:

- **Inloggning och sessioner:** e-post och lösenord. `POST /api/auth/login` ger en slumpad token som gäller i `SESSION_TTL_MINUTES` minuter. Den skickas som `Authorization: Bearer <token>`. I databasen sparas bara en sha256-hash av token, och lösenord hashas med scrypt.
- **Användarhantering:** admins skapar och tar bort användare på fliken Users. Kräver att inloggning är på.

**Slå på och av:**
- I `local` och `test` finns fliken **Config** i frontend (`PUT /api/config`). Valet sparas i tabellen `app_settings` och går före `.env`.
- I `staging` och `production` finns ingen config-sida. Där gäller bara `AUTH_ENABLED` och `USER_MANAGEMENT_ENABLED`.

**Staging och produktion:** utgå från `.env.production.example`. Den har `APP_ENV=production`, påslagen inloggning och kortare TTL, och platshållare för lösenorden. För staging byter du till `APP_ENV=staging`.

**Root-admin:** sätt `ADMIN_EMAIL` och `ADMIN_PASSWORD` i `.env`. Kontot skapas när backend startar, och lösenordet uppdateras om du ändrar det i `.env`. Root-admin kan inte tas bort.

```bash
TOKEN=$(curl -s -X POST localhost:8000/api/auth/login -H "Content-Type: application/json"   -d '{"email":"admin@example.com","password":"change-me"}' | python -c "import json,sys; print(json.load(sys.stdin)['access_token'])")
curl -H "Authorization: Bearer $TOKEN" localhost:8000/api/items
```

I Swagger loggar du in med `/api/auth/login`, klickar på **Authorize** och klistrar in token.

## Projektstruktur

```
.
├── docker-compose.yml
├── .env.example
├── pyproject.toml            # pytest-konfiguration
├── .claude/                  # Projektets Claude Code-skills och stack.py
├── code/
│   ├── backend/              # FastAPI (Dockerfile, requirements*.txt, app/ med routers/)
│   ├── frontend/             # React + Vite + nginx (Dockerfile, nginx.conf, src/ med components/)
│   ├── src/                  # Fristående exempelkod (kvittoräknare)
│   ├── libs/  settings/      # Delade hjälpbibliotek, inställningar och seed.sql
│   └── tests/                # pytest-tester
├── ai/                       # Journal, granskningar, prompter och diagram
└── .github/workflows/ci.yml  # CI: pytest med pgvector-databas
```

## Tester

```bash
pip install -r code/backend/requirements-dev.txt
docker compose up -d db
pytest
```

- Databastesterna använder `DATABASE_URL` (standard `postgresql+psycopg://app:app@localhost:5432/app`).
- Varje test körs i en transaktion som rullas tillbaka, så ingen data blir kvar.
- Går databasen inte att nå hoppas databastesterna över. Övriga tester körs ändå.
- I CI startas en pgvector-databas som service-container, så där körs alla tester.

## Bygga vidare

- **Ny resurs:**
  1. Lägg till en modell i `models.py` och scheman i `schemas.py`.
  2. Lägg till en router i `app/routers/` och registrera den i `main.py`. Eller kör `/new-resource <namn>`.
  3. Skriv tester i `code/tests/`.
- **Riktiga embeddings:** sätt `EMBEDDING_DIM` till modellens längd och räkna fram vektorerna i backend innan de sparas.
- **Snabbare vektorsökning:** lägg till ett HNSW-index när datamängden växer, till exempel `CREATE INDEX ON items USING hnsw (embedding vector_cosine_ops)`.
- **Migreringar:** byt `create_all` mot Alembic när schemat börjar ändras i en databas som redan används.
- **Fler tjänster:** lägg till dem i `docker-compose.yml`, till exempel en worker eller Redis. De når varandra via tjänstnamnet.
- **Produktion:** byt lösenord, ta bort portmappningen för `db` och lägg till CORS eller autentisering efter behov.

## Claude Code-skills för stacken

Projektets egna skills ligger i `.claude/skills/` och följer med när mallen kopieras. De använder hjälpskriptet `.claude/scripts/stack.py`, som bara behöver standardbiblioteket.

| Skill | Gör |
|---|---|
| `/stack up\|down\|status` | Startar stacken med portkoll (föreslår lediga portar i `.env`), väntar tills db är healthy och API:t svarar och visar URL:erna. `down` raderar aldrig data |
| `/stack-test` | Kör pytest i en Python-container mot riktiga databasen (som CI) och bygger frontend |
| `/diagnose` | Samlar status, healthchecks, portar och loggar och föreslår en åtgärd. Ändrar ingenting |
| `/db` | SQL via psql. Läsläge som standard, `/db --write` först efter godkännande. Underkommandon `schema`, `sample <tabell>` och `explain <sql>`, eller en fråga på svenska |
| `/seed` | Laddar exempeldata med vektorer från `code/settings/seed.sql`. Kan köras flera gånger |
| `/db-snapshot save\|restore\|list` | `pg_dump`/`pg_restore` till `backups/` (gitignorerad) |
| `/db-reset` | Raderar databasvolymen, startar om och seedar. Frågar först |
| `/new-resource <namn>` | Ny tabell med API-router, tester och React-komponent enligt mönstret för `items` |

Globalt i `~/.claude/` (inte i repot) finns också:
- **`/new-project <namn>`:** skapar ett nytt projekt från mallen, med nytt namn, lediga portar och git med `main`, `test` och `staging`.
- **Hooken `docker_guard`:**
  - ber om bekräftelse för `down -v`, `volume rm/prune`, `system prune`, `DROP`/`TRUNCATE`, `dropdb` och `pg_restore --clean`
  - stoppar `docker stop/rm/kill` på containrar som hör till andra compose-projekt

## Arbetsflöde med git

`feature/<namn>` → `test` → `staging` → `main` (merge till `main` = release, tagg `vX.Y.Z`)

| Steg | Med Claude Code | Manuellt / andra verktyg (t.ex. Copilot) |
|---|---|---|
| Skapa gren | `/branch <namn>` | `git fetch && git switch -c feature/<namn> --no-track origin/test` |
| Granska före commit | `/check-result` → `ai/reviews/` | Skriv en `ai/reviews/check-result-*.md` för hand |
| Journal | journal-hooken + `/journal` → `ai/journal/` | Skriv sammanfattningen för hand |
| PR mot test | `/pr` | `git push -u origin feature/<namn>` och sedan `gh pr create --base test` |
| Befordra | `/promote staging` / `/promote main` | `gh pr create --base staging --head test` / `gh pr create --base main --head staging` |

### Vad som skyddar flödet

- **Bara Claude Code:** hooks `branch_guard` (ingen commit/push på `main`, `staging` eller `test`) och `commit_gate` (kräver aktuell granskning). Skills och hooks ligger globalt i `~/.claude/` och finns inte i repot.
- **Alla verktyg:** CI (`.github/workflows/ci.yml`) kör pytest på PR:er och kräver en `ai/reviews/check-result-*.md` när `code/` ändras i PR:er mot `test`.
