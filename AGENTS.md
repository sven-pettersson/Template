# Template

## Om projektet
En minimal fullstack-mall att bygga vidare på: React-frontend, FastAPI-backend med Swagger och PostgreSQL med pgvector, allt i Docker Compose. Kvittoräknaren i `code/src/` finns kvar som fristående exempelkod. Se `readme.md` för beskrivning av containrarna.

## Teknik
- Backend: Python 3.14, FastAPI, SQLAlchemy, psycopg, pgvector (`code/backend/requirements.txt`)
- Frontend: React 19 + Vite, serveras av nginx (`code/frontend/package.json`)
- Databas: PostgreSQL 17 med pgvector (`pgvector/pgvector:pg17`)
- Tester: pytest (konfiguration i `pyproject.toml`, testberoenden i `code/backend/requirements-dev.txt`)

## Struktur
- `docker-compose.yml`, `.env.example` – tjänsterna `db`, `backend`, `frontend` och deras inställningar
- `code/backend/` – FastAPI-appen (`app/`), Dockerfile och requirements
- `code/frontend/` – React-appen (`src/`), Dockerfile och `nginx.conf`
- `code/src/` – fristående programkod (kvittoräknaren)
- `code/tests/` – tester (pytest hittar modulerna i `src/`, `libs/`, `settings/` och `backend/` via `pyproject.toml`)
- `.claude/` – projektets Claude Code-skills och `scripts/stack.py`
- `code/libs/` – egna hjälpbibliotek som delas mellan moduler
- `code/settings/` – programinställningar (t.ex. momssatser)
- `ai/` – AI-material: `journal/`, `reviews/`, `prompts/`, `diagrams/` (se `ai/README.md`)
- Lägg ny kod och nya tester i rätt katalog ovan, aldrig i projektroten.

## Regler
- Svara mig på svenska. Kod och variabelnamn på engelska.
- Gör små ändringar. Fråga innan du lägger till nya beroenden.
- Skriv eller uppdatera tester för all ny logik.
- Kör testerna innan du säger att du är klar.
- Committa bara när jag ber om det.

## Dokumentation
- Journalen skrivs automatiskt i `ai/journal/` (ny fil efter 20 minuters inaktivitet).
- Innan commit: kör `/journal` för att lägga till en engelsk sammanfattning (AI-verktyg, promptar, ändringar, antaganden).
- Äldre promptloggar finns kvar i `ai/prompts/` som historik.
- Diagram över projektet skapas med `/mermaid` i `ai/diagrams/` (`/mermaid readme` uppdaterar även readme.md).

## Före commit
- Kör `/check-result` och åtgärda ❌-raderna i `ai/reviews/` innan commit. Claudes commit stoppas om granskningen saknas eller är inaktuell.
- `ai/` committas tillsammans med ändringen.

## Brancher och PR
- Flöde: `feature/<namn>` → `test` → `staging` → `main` (merge till main = release, taggas `vX.Y.Z`).
- Committa eller pusha aldrig direkt på `main`, `staging` eller `test` (hooken branch_guard stoppar det).
- `/branch <namn>` skapar en arbetsgren från `test`.
- `/pr` skapar en PR mot `test` med journal och granskning i PR-texten. Den mergar aldrig.
- `/promote staging|main` skapar en befordrings-PR och föreslår en release-tagg för main.
- CI (`.github/workflows/ci.yml`) kör pytest på PR:er och kräver en `ai/reviews/check-result-*.md` när `code/` ändras i PR:er mot `test`.

## Skills för stacken
- Projektets skills finns i `.claude/skills/`: `/stack`, `/stack-test`, `/diagnose`, `/db`, `/seed`, `/db-snapshot`, `/db-reset` och `/new-resource`. Hjälpskriptet är `.claude/scripts/stack.py`. Se tabellen i readme.md.
- Använd `/db` i läsläge för att titta i databasen. Skriv bara med `/db --write` efter mitt godkännande.
- Nya resurser följer mönstret för `items`: modell, scheman, `app/routers/<namn>.py`, tester och `src/components/<Namn>.jsx`.
- Stoppa eller ta aldrig bort containrar från andra compose-projekt. Hooken docker_guard stoppar det.

## Kommandon
- Starta allt: `docker compose up --build` (frontend http://localhost:3000, Swagger http://localhost:8000/docs)
- Stoppa: `docker compose down` (lägg till `-v` för att radera databasen)
- Portar upptagna: sätt `DB_PORT`, `BACKEND_PORT` och `FRONTEND_PORT` i `.env`
- Frontend med hot reload: `cd code/frontend && npm install && npm run dev`
- Kör tester: `pip install -r code/backend/requirements-dev.txt`, `docker compose up -d db`, `pytest` (databastester hoppas över utan databas)
- Kör kvittoräknaren: `python code/src/raknare.py`
