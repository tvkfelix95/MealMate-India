# MealMate India MVP Implementation Roadmap

The phases below are dependency-ordered. The existing responsive landing page and frontend-only onboarding wizard are treated as the initial UI foundation; their answers remain client-side until backend integration.

## 1. Product requirements and user journeys

**Objective:** Define the MVP scope, user journeys, acceptance criteria, and rules for preferences, allergies, budget, cooking constraints, five meal slots, favourites, and shopping lists.

**Dependencies:** Existing product decisions, landing page, onboarding UI, and architecture boundaries.

**Completion criteria:** Reviewed requirements cover daily and 7-day planning, South Indian recipes, all supported food preferences, error/empty states, and the transition from onboarding to a personalised plan.

## 2. Database schema and relationships

**Objective:** Design PostgreSQL entities and relationships for users, preferences, recipes, ingredients, nutrition sources, meal plans, shopping lists, and favourites.

**Dependencies:** Approved requirements and user journeys.

**Completion criteria:** Schema documentation defines keys, relationships, constraints, serving context, allergen data, ownership, and migration boundaries without inventing food or nutrition data.

## 3. FastAPI backend and authentication

**Objective:** Create the API foundation, Supabase authentication integration, backend validation, authorisation, and secure user-data access.

**Dependencies:** Approved schema and Supabase project configuration.

**Completion criteria:** Authenticated API boundaries are documented and tested; backend validation and allergy restrictions are enforced; secrets use environment variables; the frontend never accesses PostgreSQL directly.

## 4. Ingredient, recipe and nutrition data

**Objective:** Import a small, verified South Indian MVP catalogue with ingredients, quantities, steps, timings, allergens, serving sizes, and nutrition sources.

**Dependencies:** Database schema, backend data-access layer, and approved data sources.

**Completion criteria:** Every published recipe has traceable ingredient and nutrition provenance, complete allergen metadata, beginner-friendly instructions, and valid serving context.

## 5. Frontend and onboarding integration

**Objective:** Connect the existing landing page and onboarding wizard to authenticated backend APIs while preserving the current responsive design and frontend/backend separation.

**Dependencies:** Backend authentication endpoints, user preference endpoints, and validated data contracts.

**Completion criteria:** Users can sign in, submit onboarding answers, safely resume or update preferences, and receive clear loading, validation, error, and empty states. No answers are persisted only in frontend state after integration.

## 6. Rule-based meal-planning engine

**Objective:** Generate daily and 7-day plans for breakfast, morning snack, lunch, evening snack, and dinner using preferences, allergies, budget, time, skill, equipment, cuisine, and recipe availability.

**Dependencies:** Verified recipe data, user preferences API, and backend service boundaries.

**Completion criteria:** Plans are deterministic and explainable, exclude restricted ingredients, respect supported constraints where data permits, and return explicit fallback or no-match responses rather than unsafe guesses.

## 7. Shopping lists and favourites

**Objective:** Let users save recipes, manage favourites, and generate shopping lists from selected daily or weekly plans.

**Dependencies:** Meal-plan engine, recipe/ingredient relationships, authenticated user storage, and frontend integration.

**Completion criteria:** Users can add/remove favourites, generate a deduplicated list with quantities and units, and view or update list state without crossing user ownership boundaries.

## 8. Testing, security and deployment

**Objective:** Validate the complete MVP and prepare a secure deployable release.

**Dependencies:** All previous phases and documented environment configuration.

**Completion criteria:** Frontend, backend, integration, validation, allergy, authorisation, and planning tests pass; secrets and production settings are checked; accessibility and responsive behaviour are reviewed; deployment, rollback, monitoring, and data-source documentation are complete.
