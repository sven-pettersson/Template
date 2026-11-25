---
name: stack
description: Startar, stoppar och visar status för projektets Docker Compose-stack (db, backend, frontend). "up" kontrollerar portkrockar och föreslår lediga portar i .env, bygger, väntar tills db är healthy och /api/health svarar och skriver ut URL:erna. "down" stoppar utan att radera databasen. "status" visar läget. Använd när användaren kör /stack, vill starta/stoppa appen eller undrar om den kör.
---

# /stack up | down | status

Hjälpskriptet `.claude/scripts/stack.py` gör det mesta. Kör allt från projektroten med Bash-verktyget.

## `/stack up` (standard om inget argument ges)

1. **Portar:** kör `python .claude/scripts/stack.py ports`.
   - Exit 0: portarna är lediga, gå vidare.
   - Exit 1: visa vilka portar som är upptagna och förslagen. Fråga om förslagen ska skrivas till `.env`. Vid ja: `python .claude/scripts/stack.py ports --write`.
   - Varnar skriptet för att portarna är satta i skalets miljö, säg att de går före `.env`.
   - Stoppa aldrig containrar från andra projekt för att frigöra en port.
2. **Bygg och starta:** `docker compose up --build -d` med timeout 600000.
   - Om bygget avbryts med `DeadlineExceeded`, `TLS handshake timeout` eller `failed to fetch` för en image: hämta base-images med `docker pull -q` (`pgvector/pgvector:pg17`, `python:3.14-slim`, `node:24-alpine`, `nginx:alpine`) och försök **en** gång till.
   - Vid andra byggfel: visa felet och föreslå `/diagnose`.
3. **Vänta:** `python .claude/scripts/stack.py wait`. Om skriptet säger TIMEOUT eller FEL: kör `/diagnose` och rapportera.
4. **Klart:** `python .claude/scripts/stack.py urls`. Visa URL:erna för användaren.

Vill användaren bara starta en del (t.ex. `/stack up db`): `docker compose up -d db`, och hoppa över API-väntan.

## `/stack down`

- Kör `docker compose down`. Databasvolymen finns kvar.
- Lägg **aldrig** till `-v`. Vill användaren rensa databasen hänvisar du till `/db-reset`.

## `/stack status`

- `docker compose ps` och `python .claude/scripts/stack.py urls`.
- Svara kort: vilka tjänster som kör och om de är healthy, samt URL:erna.
- Ser något fel ut, föreslå `/diagnose`.
