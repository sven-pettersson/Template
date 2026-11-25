---
name: db-reset
description: Raderar projektets databasvolym och startar om stacken med en tom databas, och laddar sedan exempeldata. Destruktivt – kräver uttryckligt ja. Använd när användaren kör /db-reset, vill börja om med en tom databas, eller efter att EMBEDDING_DIM eller databaslösenordet ändrats.
---

# /db-reset – börja om med tom databas

**Det här raderar all data i projektets databas.**

1. **Visa vad som försvinner:** kör `/db` i läsläge med `SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY 1;` om db kör. Volymen heter `<projekt>_pgdata`; projektnamnet får du med `python .claude/scripts/stack.py env`.
2. **Erbjud en backup:** "Vill du spara en snapshot först (`/db-snapshot save före-reset`)?"
3. **Fråga och vänta på ett uttryckligt ja.** Ett "kanske" eller ett svar på en annan fråga räcker inte.
4. **Kör:**
   ```bash
   docker compose down -v
   ```
   Hooken docker_guard ber om bekräftelse en gång till. Det är meningen.
5. **Starta igen:** följ `/stack up`, med portkoll, bygge och väntan.
6. **Seed:** fråga om exempeldata ska laddas. Vid ja: följ `/seed`.
7. **Bekräfta** att databasen är tom eller seedad och visa URL:erna.
