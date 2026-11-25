---
name: diagnose
description: Felsöker projektets Docker-stack utan att ändra något. Samlar status, healthchecks, portkrockar, svar från /api/health (direkt och via nginx) och loggar från tjänster med problem, och ger en kort diagnos med förslag på åtgärd. Använd när användaren kör /diagnose, när /stack up misslyckas, när appen inte svarar eller när en container startar om.
---

# /diagnose – felsök stacken

**Ändra ingenting.** Inga omstarter, inga filändringar och ingen `down`. Föreslå åtgärder och låt användaren välja.

1. **Samla fakta:** `python .claude/scripts/stack.py diagnose`. Skriptet ger:
   - en tabell med tjänsterna (state och health)
   - portkollen
   - hälsokontroller mot backend direkt och via frontend/nginx
   - loggar från tjänster som inte kör, är unhealthy eller har fel i loggen
2. **Behövs mer:** `docker compose logs --tail 200 <tjänst>` eller `docker compose config` (den effektiva konfigurationen, inklusive värden från `.env`).
3. **Vanliga orsaker att känna igen:**

   | Symtom | Trolig orsak | Förslag |
   |---|---|---|
   | `port is already allocated` | Ett annat projekt använder porten | `python .claude/scripts/stack.py ports --write`, sedan `/stack up` |
   | backend `exited`, `OperationalError`/`connection refused` | db inte redo eller fel `DATABASE_URL` | Kontrollera db health och variablerna i `.env` |
   | `password authentication failed` | `.env` ändrades efter att volymen skapades | Återställ lösenordet eller `/db-reset` (raderar data) |
   | `expected N dimensions, not M` | `EMBEDDING_DIM` ändrad mot en befintlig tabell | `/db-reset`, eller ändra tillbaka `EMBEDDING_DIM` |
   | backend svarar, frontend ger 502 | nginx når inte `backend:8000` | Kör backend-containern? Stämmer `nginx.conf`? |
   | `ModuleNotFoundError` i backend | Paket saknas i `requirements.txt` eller imagen inte ombyggd | `docker compose up --build -d backend` |
   | `DeadlineExceeded` vid bygge | Nätverkstimeout vid image-hämtning | `docker pull` av base-imagen och bygg igen |

4. **Svara** med:
   - **Läge:** en rad per tjänst.
   - **Diagnos:** den troligaste orsaken, med citat ur loggen som belägg.
   - **Åtgärd:** konkreta kommandon i ordning. Markera åtgärder som raderar data.
