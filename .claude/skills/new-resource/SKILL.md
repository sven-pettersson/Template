---
name: new-resource
description: Lägger till en ny resurs (tabell + API + tester + frontend-vy) i mallens stack enligt samma mönster som items - SQLAlchemy-modell, Pydantic-scheman, APIRouter i code/backend/app/routers/, transaktionstester i code/tests/ och en React-komponent. Frågar efter fält först. Använd när användaren kör /new-resource <namn> eller vill lägga till en ny entitet, tabell eller endpoint.
---

# /new-resource <namn>

Mönstret som ska följas är `items`. Läs de här filerna innan du skriver något:
- `code/backend/app/models.py`
- `code/backend/app/schemas.py`
- `code/backend/app/routers/items.py`
- `code/backend/app/main.py`
- `code/tests/test_backend_api.py`
- `code/frontend/src/components/Items.jsx`
- `code/frontend/src/App.jsx`

## 1. Namn och fält
- **Namn:** engelska. Klassen blir singular PascalCase (`Customer`), tabellen och URL:en plural snake/kebab (`customers`, `/api/customers`), och filerna heter `routers/customers.py` och `components/Customers.jsx`.
- **Fråga efter fälten** i en enda fråga, med ett förslag utifrån namnet: namn, typ (`str`, `text`, `int`, `float`, `bool`, `date`, `datetime`, `vector`), obligatoriskt eller valfritt, och unikt.
  - Typerna mappas till `String(n)`, `Text`, `Integer`, `Float`, `Boolean`, `Date`, `DateTime` och `Vector(EMBEDDING_DIM)`.
- **Relationer** (`<annan>_id` som `ForeignKey`): fråga vilken tabell, och om radering ska kaskadera.
- Fråga också om resursen ska ha en vektorkolumn och sökning, som `items/search`.

## 2. Backend
1. `models.py`: en ny klass med `Mapped[...]` och `mapped_column(...)`, i samma stil som `Item`.
2. `schemas.py`: `<Namn>Create` och `<Namn>Read`, plus `<Namn>Update` om användaren vill ha PUT/PATCH. Återanvänd `_check_dim` för vektorer och lägg till validering (`Field(min_length=…)`, `ge=`) där det är rimligt.
3. `routers/<plural>.py`:
   - `APIRouter(prefix="/api/<plural>", tags=["<plural>"])`
   - `GET ""` listar och `POST ""` skapar (201)
   - `GET "/{id}"` ger 404 med `HTTPException` om raden saknas
   - `DELETE "/{id}"` ger 204
   - PUT/PATCH och search bara om användaren vill ha dem
4. `main.py`: `from app.routers import <plural>` och `app.include_router(<plural>.router, dependencies=[Depends(require_login)])`, så att resursen kräver Bearer-token när inloggning är påslagen.
5. **Inga migreringar finns.** `create_all` skapar nya tabeller men ändrar aldrig befintliga. Säg det om resursen ändrar en befintlig tabell, och föreslå `/db-reset` i dev.

## 3. Tester – `code/tests/test_<plural>_api.py`
- Återanvänd fixturerna i `code/tests/api_fixtures.py` (`client`, `db_client`, `db_session`, `auth_on`, `make_user`, `login`). Lägg till den nya tabellen i `DELETE FROM`-raderna i `db_session`.
- Testa också att endpointsen ger 401 utan token när inloggning är på (`auth_on`), och att de fungerar med `login(...)`.
- Testa:
  - skapa och lista
  - hämta en rad och 404 när den saknas
  - radera
  - valideringsfel (422) för varje regel
  - kantfall: tomma strängar, gränsvärden och fel vektorlängd

## 4. Frontend
- `components/<Plural>.jsx`: kopiera mönstret från `Items.jsx`, med en lista och ett formulär för de obligatoriska fälten. Använd `getJson` och `postJson` från `src/api.js`.
- `App.jsx`: importera komponenten och lägg den under `<Items />`.

## 5. Kontrollera
1. Bygg om backend och frontend med `docker compose up --build -d backend frontend` och vänta med `python .claude/scripts/stack.py wait`.
2. Kör `/stack-test`. Allt ska vara grönt.
3. Visa de nya endpointsen i Swagger (`/docs`).

Gör ingen commit. Påminn om `/journal`, `/check-result`, commit och `/pr`.
