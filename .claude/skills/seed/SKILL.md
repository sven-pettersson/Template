---
name: seed
description: Laddar exempeldata (items med vektorer) från code/settings/seed.sql i projektets databas. Kan köras flera gånger utan dubbletter. Använd när användaren kör /seed, vill ha testdata eller exempeldata för att prova vektorsökningen.
---

# /seed – exempeldata

1. **Förutsättningar:** backend måste ha startat minst en gång, eftersom den skapar tabellerna och tillägget `vector`. Kontrollera med `docker compose ps`. Kör inte db eller backend, fråga om `/stack up`.
2. **Vektorlängd:** seed-filen har vektorer med 3 värden. Kontrollera `EMBEDDING_DIM` med `python .claude/scripts/stack.py env`. Är den inte 3: säg att seed-filen inte passar och erbjud att skriva en ny med rätt längd. Kör inte filen.
3. **Kör:**
   ```bash
   docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -q' < code/settings/seed.sql
   ```
   Kör via Bash-verktyget, eftersom omdirigeringen `<` inte fungerar i Windows PowerShell 5.1.
4. **Visa:** antalet items efteråt och ett exempel på sökning som går att prova i Swagger (`POST /api/items/search` med `{"embedding": [1, 0, 0], "limit": 3}`). Den ska ge Apple och Banana först.

Användaren kan lägga till egen data i `code/settings/seed.sql`. Behåll mönstret `WHERE NOT EXISTS`, så att filen kan köras flera gånger.
