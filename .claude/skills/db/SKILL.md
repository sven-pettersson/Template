---
name: db
description: Kör SQL mot projektets PostgreSQL/pgvector-databas i Docker via psql. Läsläge som standard; skrivning bara med --write efter att SQL:en visats och godkänts. Underkommandon schema, sample <tabell>, explain <sql>, eller en fråga på svenska som översätts till SQL. Använd när användaren kör /db, vill titta i databasen, räkna rader, se schemat eller testa en SQL-fråga.
---

# /db – SQL mot databasen

Databasen körs i compose-tjänsten `db`. Användare och databas läses från containerns egna miljövariabler, så du behöver inga lösenord.

## Grundkommandon

Kör alltid via **Bash-verktyget** från projektroten och skicka SQL:en på stdin med en heredoc.

**Läsläge (standard):**
```bash
docker compose exec -T -e PGOPTIONS="-c default_transaction_read_only=on" db \
  sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -P pager=off' <<'SQL'
<SQL här>
SQL
```

**Skrivläge** (bara med `--write`) är samma kommando, men utan `-e PGOPTIONS=...`.

Får du `service "db" is not running`, säg det och föreslå `/stack up`. Starta inte stacken själv.

## Läge efter argument

| Argument | Gör |
|---|---|
| `schema` | `\dt` och `\d+ <tabell>` för varje tabell, plus `\dx` för installerade tillägg. Visa vektorkolumner (`vector(n)`) och index tydligt. |
| `sample <tabell>` | `SELECT * FROM <tabell> ORDER BY 1 LIMIT 10;`. Långa vektorer kortas i sammanfattningen. |
| `explain <sql>` | `EXPLAIN (ANALYZE, BUFFERS) <sql>` i läsläge. Förklara planen kort, till exempel om ett HNSW-index används eller om det blir Seq Scan. |
| ren SQL | Kör den i läsläge. |
| fråga på svenska | Läs först `schema` om du inte redan känner till tabellerna. Skriv SQL:en, **visa den** och kör den sedan i läsläge. |
| `--write <sql/fråga>` | Se nedan. |

## Skrivning (`--write`)

1. Visa exakt den SQL som ska köras och säg vilka tabeller och ungefär hur många rader som påverkas. Kör gärna en `SELECT count(*)` med samma `WHERE` i läsläge först.
2. Fråga användaren och vänta på ett ja.
3. Kör SQL:en i en transaktion (`BEGIN; … COMMIT;`) i skrivläge.

Regler:
- Slå aldrig av läsläget inifrån SQL (`SET default_transaction_read_only = off`, `SET TRANSACTION READ WRITE`).
- `DROP` och `TRUNCATE` stoppas även av hooken docker_guard, som kräver bekräftelse.
- Schemaändringar hör hemma i `code/backend/app/models.py` och inte i manuell SQL. Säg till om användaren försöker ändra schemat med `/db`.

## Svar

Visa resultatet som en tabell, plus en mening om vad det betyder. Vid fel: visa felmeddelandet och föreslå en rättning.
