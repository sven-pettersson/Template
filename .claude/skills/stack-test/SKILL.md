---
name: stack-test
description: Kör projektets pytest-tester i en python:3.14-slim-container på compose-nätverket mot den riktiga databasen (som i CI), och bygger frontend som byggtest. Kräver inget lokalt Python eller npm. Använd när användaren kör /stack-test, vill köra testerna "som i CI" eller när lokala tester hoppar över databastesterna.
---

# /stack-test [pytest-argument]

1. **Kontrollera stacken:** `docker compose ps --status running --services`. Om `db` saknas: fråga om stacken ska startas med `/stack up`. Utan databas körs testerna ändå, men databastesterna hoppas över. Säg det tydligt.
2. **Backend och Python-tester:**
   ```bash
   python .claude/scripts/stack.py test <pytest-argument>
   ```
   Kör med timeout 600000. Första körningen installerar beroenden; pip-cachen sparas i volymen `<projekt>_pipcache`.
   - Testerna körs mot samma databas som appen. Varje databastest körs i en transaktion som rullas tillbaka, så data påverkas inte.
   - Exempel på argument: `-q`, `-k search`, `code/tests/test_backend_api.py`.
3. **Frontend-bygge** (hoppa över om användaren bara gav pytest-argument som pekar på ett enskilt test):
   ```bash
   python .claude/scripts/stack.py build-frontend
   ```
4. **Rapportera:** antal passed, failed och skipped, och skälen till skip (`-rs` visar dem). Säg om frontend-bygget lyckades. Vid fel: visa felet i testet och vad det troligen beror på. Ändra ingen kod utan att användaren ber om det.
