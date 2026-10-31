# Initial Architecture Notes

## Responsibility boundaries

### Frontend

The frontend will render screens, collect user input, call the backend API, and display meal plans, recipes, nutrition, budgets, and grocery lists. It must not connect directly to PostgreSQL.

### Backend

The backend will authenticate requests, apply business rules, validate input, calculate or retrieve meal-plan results, and expose a documented API. It will own access to the database.

### Database

The database will persist users, recipes, ingredients, nutrition data, preferences, meal plans, budgets, and grocery-list data through controlled migrations.

### Authentication

Supabase Auth will manage identity and authentication flows. Backend authorization will still verify authenticated requests before accessing user-specific data.

#### Approved hostname and JWT architecture

- The default Supabase project domain remains the canonical JWT issuer and JWKS source.
- `SUPABASE_URL` remains supported for backward compatibility with the current implementation.
- Future production configuration should separate the server-only Supabase Auth REST base URL, JWT issuer and JWKS URL. These values must be configured by the server and must never come from request data.
- A Supabase custom domain may be introduced only after testing DNS, TLS, Auth REST requests, JWKS retrieval and OAuth callback flows across representative Indian ISPs. A custom API domain must not automatically be treated as the JWT issuer; the issuer must match the verified token `iss` claim.
- Backend authorization continues to use the verified Supabase user UUID. Administrator access remains database-backed through explicit admin membership, not JWT metadata, request fields or client-provided roles.
- No user-controlled authentication endpoint or JWT issuer override is permitted.

## Expansion principles

- Model cuisine as data so additional Indian cuisines can be added later.
- Model dietary preferences as extensible values rather than hard-coded screen logic.
- Keep nutrition values linked to their verified source and serving size.
- Keep user-facing language separate from domain data so Tamil can be added later.
- Keep meal-planning rules in the backend rather than duplicating them in the frontend.
