# AGENTS.md

## Project

MealMate India is a mobile-first Indian meal-planning and cooking web application for students and working professionals.

## Product scope

- Start with South Indian recipes; support expansion across Indian cuisines later.
- Support vegetarian, egg, and non-vegetarian options.
- Provide personalised daily and 7-day meal plans.
- Support five meal slots: breakfast, morning snack, lunch, evening snack, and dinner.
- Consider user-defined budget, cooking time, skill level, equipment, dietary preferences, and restrictions.
- Provide recipe ingredients, quantities, cooking steps, preparation time, cooking time, and nutrition information.
- Provide shopping lists and favourites.
- Use English first; design for Tamil support later.

## Planned stack

- Frontend: React, TypeScript, and Tailwind CSS.
- Backend: Python and FastAPI.
- Database and authentication: PostgreSQL and Supabase.

## Architecture rules

- Keep frontend, backend, authentication, and database responsibilities separate.
- The frontend presents information and collects input; it must not access PostgreSQL directly.
- The backend owns validation, authorisation, meal-planning rules, allergy enforcement, and access to user-specific data.
- Keep domain logic modular so additional cuisines, languages, dietary options, and meal-planning rules can be added without major rewrites.
- Prefer simple, reusable, maintainable designs suitable for a beginner developer.
- Avoid unnecessary dependencies, abstractions, generated files, and code.

## Safety and data integrity

- Never invent recipe, nutrition, allergen, or ingredient data.
- Nutrition values must come from a documented, verified source and include an appropriate serving context.
- Allergy restrictions must be validated and enforced by the backend, not only by the frontend.
- Do not make medical, treatment, prevention, or other medical diet claims.
- Validate and authorise all user-controlled input on the backend.
- Do not commit secrets, credentials, tokens, or private user data.
- Use environment variables for configuration and secrets.

## Development workflow

- Complete only explicitly requested tasks.
- Inspect existing files and conventions before making changes.
- Preserve unrelated user changes.
- Do not install packages or run setup commands without explaining their purpose and obtaining approval.
- Do not create application code, database tables, or migrations unless explicitly requested.
- Document significant architecture and product decisions.
- Verify changes with focused checks appropriate to the task.
- Keep responses concise and explain technical decisions in beginner-friendly language.

## Repository layout

- `frontend/` — React user interface.
- `backend/` — FastAPI API and business logic.
- `database/` — PostgreSQL design documentation and future migrations.
- `docs/` — product, architecture, and development documentation.
