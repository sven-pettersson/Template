---
name: db-snapshot
description: Sparar och återställer ögonblicksbilder av projektets databas med pg_dump/pg_restore till backups/ (gitignorerad). "save <namn>" sparar, "restore <namn>" återställer efter bekräftelse, "list" visar sparade. Använd när användaren kör /db-snapshot, vill spara databasen före ett experiment eller gå tillbaka till ett tidigare läge.
---

# /db-snapshot save | restore | list [namn]

Snapshots sparas i `backups/<namn>.dump` i projektroten. Katalogen är gitignorerad, så datan hamnar aldrig i git. Kör allt med **Bash-verktyget**: binär omdirigering förstör filen i Windows PowerShell 5.1.

Kontrollera först att `db` kör (`docker compose ps`). Gör den inte det, föreslå `/stack up`.

## `save [namn]`
- Namn saknas: använd `snapshot-YYYYMMDD-HHMM`. Gör om namnet till kebab-case.
- Finns filen redan: fråga innan den skrivs över.
```bash
mkdir -p backups
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > backups/<namn>.dump
```
Visa sedan filens storlek (`ls -lh backups/<namn>.dump`). En fil på 0 byte betyder att något gick fel: visa felet och ta bort den tomma filen.

## `list`
`ls -lt backups/*.dump` som en tabell med namn, storlek och datum.

## `restore <namn>`
1. Kontrollera att `backups/<namn>.dump` finns. Saknas namn: visa `list` och fråga.
2. Säg att nuvarande data i databasen skrivs över. Erbjud att spara en snapshot av nuläget först.
3. Vänta på ett uttryckligt ja.
4. Kör:
   ```bash
   docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner' < backups/<namn>.dump
   ```
   Hooken docker_guard ber om bekräftelse för `--clean`.
5. Kontrollera resultatet med `/db` i läsläge (antal rader per tabell).
