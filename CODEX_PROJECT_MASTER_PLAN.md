# MealMate India --- Codex Master Project Instructions & Delivery Roadmap

**Document type:** Living project instruction, implementation plan and
checkpoint register\
**Product:** MealMate India\
**Repository:** `https://github.com/tvkfelix95/MealMate-India.git`\
**Current branch:** `master`\
**Last roadmap update:** 31 October 2026\
**Status:** Active development --- foundation and deployment
established; customer application core in progress

------------------------------------------------------------------------

## 0. How Codex must use this file

This is the single living source of truth for product scope, technical
decisions, delivery order and implementation checkpoints.

### 0.1 Start-of-task procedure --- mandatory

At the beginning of every MealMate India task:

1.  Read this file completely enough to identify:
    -   Current phase and next incomplete checkpoint.
    -   Completed checkpoints and their evidence.
    -   Product constraints and architecture decisions.
    -   Dependencies and known blockers.
2.  Read the repository `AGENTS.md` and any more specific `AGENTS.md`
    files that apply to the files being changed.
3.  Inspect the relevant existing code, tests and schemas before
    editing.
4.  Check Git status before editing. Do not overwrite or discard user
    changes.
5.  Work only on the next checkpoint unless the user explicitly asks for
    another task.
6.  If a prerequisite is blocked, stop and report the blocker. Do not
    silently skip ahead or invent a workaround.
7.  Do not ask the user to repeat information already recorded here or
    in the repository.

### 0.2 End-of-task procedure --- mandatory

At the end of every task:

1.  Run the smallest relevant tests first.
2.  Run broader tests/build/lint when appropriate and practical.
3.  Report exactly what passed, failed, or was not run.
4.  Update the checkpoint table in this file:
    -   `NOT STARTED`
    -   `IN PROGRESS`
    -   `BLOCKED`
    -   `IMPLEMENTED — TESTS PENDING`
    -   `COMPLETE`
5.  A checkpoint may be marked `COMPLETE` only when:
    -   Implementation is present.
    -   Required tests/checks pass.
    -   Acceptance criteria are met.
    -   No known critical issue remains for that checkpoint.
6.  Record the evidence: test command and result, migration identifier
    if applicable, and relevant commit hash if committed.
7.  Update `Current position`, `Next action`, `Known blockers`, and
    `Last updated`.
8.  Do not mark a task complete merely because code was written or a
    build succeeded.
9.  Do not claim a deployment, migration, email, integration, or
    external action succeeded unless it was actually verified.
10. Keep the update concise. Do not duplicate the whole roadmap in the
    status section.

### 0.3 Token and context efficiency

-   Use this file as persistent project context; do not repeatedly
    regenerate project documentation.
-   Give the user one meaningful task at a time unless they explicitly
    request a batch.
-   Prefer small, focused changes and concise prompts.
-   Inspect only relevant files; expand inspection only when evidence
    requires it.
-   Do not repeatedly print large files or entire repository listings.
-   Do not rewrite working modules to achieve a small change.
-   Do not add dependencies unless necessary and approved by the project
    architecture.
-   Do not run broad automated refactors.
-   Do not run destructive commands, reset Git, force-push, or overwrite
    user work.
-   Do not run `npm audit fix --force`.
-   Do not expose, request, print, commit, or log secrets.
-   Never ask the user to paste `.env`, passwords, API keys, database
    URLs, access tokens, refresh tokens, or SMTP credentials into chat.
-   For Codex responses, report: **result, files changed, checks,
    blockers, next checkpoint**.
-   If the task is ambiguous, ask one concise clarification instead of
    making a high-impact assumption.

### 0.4 Change-control rules

Before a code change: - Identify the smallest files needed. - State the
intended behavior and acceptance criteria. - Preserve existing API
contracts unless a deliberate versioned change is approved. - Add or
update tests for changed behavior. - Consider security, privacy,
accessibility, mobile layout and failure states.

After a code change: - Review the diff. - Run `git diff --check`. -
Check that only intended files changed. - Scan changed content for
accidental secrets. - Never stage or commit unrelated or user-created
files. - Commit and push only when the user asks or has explicitly
approved that action.

------------------------------------------------------------------------

## 1. Product vision and definition

MealMate India is a mobile-first Indian meal-planning and cooking
application. It helps people decide what to cook, learn how to cook it,
plan meals within a daily/weekly budget, and turn the plan into a
practical shopping list.

It is not merely a chatbot, generic recipe directory, diet-treatment
product, or grocery marketplace.

### 1.1 Primary users

-   Indian working professionals.
-   Students and people living in PG/accommodation.
-   People newly learning to cook independently.
-   People who want practical, budget-aware Indian meal planning.
-   People who want simple, repeatable home-cooking routines.

### 1.2 Product scope and launch approach

-   Start with South Indian cuisine and expand across India.
-   English first; Tamil support later.
-   Vegetarian, egg and non-vegetarian preferences.
-   Mobile-first responsive web application.
-   Daily and seven-day meal planning.
-   Five meal slots: breakfast, morning snack, lunch, evening snack and
    dinner.
-   Initial content target: 100 reviewed recipes.
-   MVP does not provide therapeutic/medical diets or diagnose health
    conditions.

### 1.3 Product principles

1.  Useful, practical meals before flashy AI.
2.  Food safety and allergy exclusions are hard constraints.
3.  Nutrition values must be sourced and traceable; unknown values
    remain unknown.
4.  Budget estimates must show uncertainty and location/date context.
5.  Beginner-friendly cooking instructions are a core product feature.
6.  A plan must explain when the user's constraints cannot all be
    satisfied.
7.  Never silently violate allergies, diet preference, equipment
    constraints or strict time limits.
8.  AI may explain or help navigate verified content; it must not invent
    nutrition facts or override safety rules.
9.  Customers and administrators have separate experiences and
    authorization.
10. Ship reliable increments; do not claim a feature works until it is
    tested end-to-end.

------------------------------------------------------------------------

## 2. Product requirements

### 2.1 Customer journey

1.  Visit the public MealMate landing page.
2.  Create an account or log in.
3.  Verify email if the authentication configuration requires it.
4.  Complete or update food preferences.
5.  Enter the customer dashboard.
6.  Generate a daily or seven-day meal plan.
7.  Inspect recipes and cooking instructions.
8.  Replace a meal when allowed.
9.  Generate and manage a shopping list.
10. Save favourites and revisit plans.

### 2.2 Customer profile and preferences

The customer can manage:

-   Display name.
-   Food preference: vegetarian, egg, non-vegetarian.
-   Allergies.
-   Disliked ingredients.
-   Daily food budget in INR.
-   Cooking skill level.
-   Available cooking time.
-   Kitchen equipment.
-   Preferred cuisine.

Allergy and dislike lists must be stored as structured references, not
arbitrary strings where a controlled ingredient/allergen record is
required.

### 2.3 Recipe requirements

Each reviewed recipe should support:

-   Stable recipe identifier and slug.
-   Name and description.
-   Cuisine and meal category.
-   Diet classification.
-   Serving count and serving size.
-   Preparation and cooking time.
-   Ingredient quantities and units.
-   Ingredient raw/cooked state.
-   Edible quantity where known.
-   Ordered cooking steps.
-   Equipment requirements.
-   Allergen mapping.
-   Nutrition data and provenance.
-   Recipe version.
-   Publication status.
-   Image/media rights and source where media is used.

### 2.4 Meal plan requirements

-   Daily and seven-day plans.
-   Five meal slots per day.
-   User servings/household size where supported.
-   Allergy and diet filters applied before ranking.
-   Budget and cooking-time feasibility.
-   Equipment compatibility.
-   Recipe variety and repetition controls.
-   Ingredient overlap to reduce waste where useful.
-   Clear reasons when no valid plan can be produced.
-   Regeneration/replacement must preserve hard constraints.

### 2.5 Shopping list requirements

-   Aggregate ingredient quantities across selected meals.
-   Preserve compatible units and avoid unsafe unit conversions.
-   Group items into useful categories.
-   Show estimated price, location, source and date where available.
-   Distinguish quantity consumed from package quantity purchased when
    package data exists.
-   Allow purchased/checked state.
-   Avoid claiming exact current prices without current data.

------------------------------------------------------------------------

## 3. Architecture and technical decisions

### 3.1 Current stack

**Frontend** - Vite - React - TypeScript - Tailwind CSS - Mobile-first
responsive web UI

**Backend** - Python - FastAPI - Pydantic - SQLAlchemy - Alembic -
Pytest

**Data and identity** - Supabase PostgreSQL - Supabase Auth - Row Level
Security (RLS) - Backend verifies Supabase JWTs and enforces
ownership/authorization.

**Hosting** - Render backend web service. - Render static frontend. -
Supabase project in Mumbai region (`ap-south-1`).

### 3.2 Repository structure

Existing project root is `MealPlanner`; product name is MealMate India.

Expected key areas: - `frontend/` --- customer-facing web application. -
`backend/` --- FastAPI API and business logic. - `database/` ---
database notes/design where present. - `docs/` --- architecture, product
requirements, roadmap and data documentation. - `AGENTS.md` ---
repository-level agent guidance. - This file --- detailed living project
roadmap and checkpoint register.

Inspect actual paths before assuming a file exists.

### 3.3 Environment and deployment

-   Local frontend development server previously used port 5173.
-   Local FastAPI server previously used port 8000.
-   API prefix: `/api/v1`.
-   Backend health endpoint: `/api/v1/health`.
-   Frontend production URL currently:
    `https://mealmate-india-web.onrender.com`.
-   Backend production URL currently:
    `https://mealmate-india-api.onrender.com`.
-   Supabase project URL is configured through environment variables; do
    not hardcode secrets or credentials.
-   Render CORS origin must exactly match the actual frontend origin.
-   Never run database migrations automatically on application startup.
-   Apply migrations deliberately and verify the resulting Alembic
    revision.
-   Render free services may sleep; treat current deployment as a
    test/staging deployment until production reliability is explicitly
    addressed.

### 3.4 Authentication and authorization

-   Supabase is the identity provider.
-   Backend validates JWT signature, issuer, audience, expiry and
    subject.
-   The verified Supabase user UUID is the identity key.
-   Passwords are sent to Supabase Auth only; never stored in
    application tables.
-   Access tokens are held in browser `sessionStorage` under the
    existing frontend convention unless a security review approves a
    better design.
-   Never trust a client-supplied user ID or role.
-   Customer endpoints derive ownership from the verified JWT subject.
-   Admin endpoints require verified identity plus server-side
    membership in `admin_users`.
-   RLS is enabled on application tables; backend ownership checks
    remain mandatory because privileged database roles can bypass RLS.
-   Admin bootstrap is a controlled one-time server-side process, not a
    public customer registration feature.
-   Do not expose admin bootstrap controls in the public customer
    journey.

### 3.5 Customer and admin separation

**Customer application** - Public landing page. - Customer
sign-up/login. - Profile and preferences. - Onboarding. - Meal
dashboard. - Recipes, plans, shopping lists and favourites.

**Administrator application** - Separate restricted interface and
route/deployment. - No admin setup button in public customer
navigation. - Admin-only access enforced on the backend, not merely
hidden in the UI. - Shared backend/database may be used, but each admin
API must enforce `require_admin`. - Admin interface must not permit
self-promotion or role selection. - First administrator is provisioned
through the controlled bootstrap process already implemented on the
backend. - A separate admin subdomain can be introduced when
domain/hosting setup is ready; do not assume it already exists.

### 3.6 Data and nutrition integrity

-   Preserve missing nutrient values as `NULL`, never substitute zero.
-   Store nutrition source/provenance.
-   Keep raw and cooked ingredient states distinct.
-   Version recipes and associated nutrition.
-   Recipe nutrition must refer to the exact recipe version.
-   Publication readiness must validate ingredients, allergen mappings,
    nutrition provenance and required instructions.
-   Calculation principle: nutrient contribution = edible grams / 100 ×
    nutrient value per 100g; sum ingredient contributions; divide by
    servings as appropriate.
-   Account for oil, sauces, additions, edible portions and cooking
    yield where known.
-   Store precision; round only for display.
-   Do not invent values to fill gaps.

### 3.7 Food data and licensing

-   IFCT 2017 and INDB have been considered as Indian food-data sources;
    commercial reuse rights must be confirmed before using their data in
    a commercial product.
-   USDA FoodData Central may supplement gaps; verify the exact
    data/source and retain provenance.
-   Recipe text and food images have separate licensing requirements.
-   Do not scrape recipes or images.
-   Record rights/source for every externally sourced media asset and
    recipe content.
-   Do not publish illustrative test fixtures as production recipes.

### 3.8 Price data

-   Prices are location- and time-dependent.
-   Store ingredient, unit, location, observation date, source and
    confidence.
-   Estimate cost using quantity × unit price with compatible units.
-   Clearly distinguish estimates from live prices.
-   Do not promise exact prices without a reliable fresh source.
-   Avoid integrating a grocery provider until its terms, coverage and
    technical API are verified.

------------------------------------------------------------------------

## 4. Development workflow and definition of done

For each checkpoint, Codex must:

1.  Read this master plan and relevant `AGENTS.md`.
2.  Inspect existing implementation and tests.
3.  Describe the smallest safe change.
4.  Implement only the requested checkpoint.
5.  Add/update tests.
6.  Run focused tests.
7.  Run relevant broader tests, lint and build.
8.  Review the diff and check for accidental secrets.
9.  Update this master plan's checkpoint status and evidence.
10. Report changed files, test results, blockers and next checkpoint.

### Definition of done

A feature is not complete until: - Happy path works. - Validation and
error paths work. - Authorization and ownership are tested where
relevant. - Data persistence is verified where relevant. -
Mobile/responsive behavior is checked for UI changes. - Accessibility
basics are considered. - Tests pass. - No unrelated regressions are
known. - Documentation and this checkpoint file are updated.

------------------------------------------------------------------------

## 5. Delivery roadmap --- foundation to enterprise

The phases are ordered by dependency. Do not jump ahead just because a
later feature sounds attractive.

### Phase 0 --- Product and engineering foundation

**Goal:** Establish the project structure, decisions, database and
deployment baseline.

-   [x] Product direction and initial requirements documented.
-   [x] Repository and GitHub remote established.
-   [x] Frontend Vite/React/TypeScript/Tailwind foundation.
-   [x] FastAPI backend foundation.
-   [x] PostgreSQL/SQLAlchemy connection infrastructure.
-   [x] Alembic migration setup.
-   [ ] Initial MVP schema migration applied (migration exists; live
    Supabase application is not verified in this repository).
-   [ ] RLS migration applied (migration exists; live Supabase application
    is not verified in this repository).
-   [x] Supabase JWT verification.
-   [x] Supabase register/login/logout API foundation.
-   [x] Profile API foundation.
-   [x] Preferences API foundation.
-   [x] Food-data models and validation foundation.
-   [x] Recipe import schemas and transactional import service.
-   [x] Admin membership model and authorization dependency.
-   [x] One-time admin bootstrap backend.
-   [x] CORS configuration.
-   [x] Frontend lockfile and build.
-   [x] Initial GitHub commit/push.
-   [ ] Render backend and frontend test deployments (deployment state is
    not verified in this repository).
-   [x] Privacy-safe Supabase Auth diagnostics added and pushed.
-   [x] Supabase signup failure diagnosed as email rate limit
    (`429 email rate limit exceeded`).
-   [ ] Configure production-capable custom SMTP and verify end-to-end
    email delivery.
-   [ ] Correct backend mapping so provider HTTP 429 is returned as an
    appropriate client-facing rate-limit response, not a misleading 503.
-   [ ] Review current Render deployment, CORS and environment
    configuration before public testing.

**Acceptance:** Development environment and test deployment are
reproducible; authentication provider connectivity and email delivery
are verified; no secret is committed.

### Phase 1 --- Customer application foundation

**Goal:** A customer can create an account, configure preferences and
reach a protected dashboard. Admin setup is not part of the customer
journey.

#### 1A. Separate customer and admin experiences

-   [x] Inspect existing frontend architecture and flows.
-   [x] Remove Administrator Setup from public landing navigation.
-   [x] Add customer Login and Create Account entry points.
-   [x] Add isolated `CustomerAuth.tsx` component.
-   [x] Preserve existing admin component/backend controls separately.
-   [ ] Decide and implement the dedicated admin route/app boundary
    without exposing it in customer navigation.
-   [ ] Verify customer routes cannot access admin functions.
-   [ ] Verify backend admin protection remains effective regardless of
    frontend visibility.

#### 1B. Customer authentication

-   [x] Customer registration UI wired to existing backend auth utility.
-   [x] Customer login UI wired to existing backend auth utility.
-   [x] Session token handling follows existing `sessionStorage`
    convention.
-   [x] Loading and common auth error messages.
-   [ ] Verify custom SMTP email delivery.
-   [ ] Test new account registration with a real test email.
-   [ ] Test email verification and resend behavior if supported.
-   [ ] Test login before and after verification according to Supabase
    settings.
-   [ ] Test logout and session expiration.
-   [ ] Test duplicate email, invalid credentials, provider outage and
    429.
-   [ ] Ensure errors are actionable and do not leak provider internals.
-   [ ] Review token/session handling and browser security implications.

#### 1C. Profile and preferences persistence

-   [ ] Inspect current profile/preferences API contracts and frontend
    schemas.
-   [ ] Add display-name collection and validation.
-   [ ] Save display name using `PATCH /api/v1/profile/me`.
-   [ ] Save preferences using `PUT /api/v1/preferences/me`.
-   [ ] Map food preference correctly: vegetarian, egg, non-vegetarian.
-   [ ] Map allergies to known backend references.
-   [ ] Map disliked ingredients to known backend references.
-   [ ] Save daily budget in INR with positive/range validation.
-   [ ] Save cooking skill.
-   [ ] Save available cooking time.
-   [ ] Save kitchen equipment.
-   [ ] Save preferred cuisine according to current backend schema
    (currently one preferred cuisine; do not send multiple without a
    schema change).
-   [ ] Handle loading, validation, network and authorization errors.
-   [ ] Preserve answers when navigating backward.
-   [ ] Do not lose answers on a recoverable API failure.
-   [ ] Verify persisted data by reloading and retrieving
    profile/preferences.
-   [ ] Test that one customer cannot read or update another customer's
    profile/preferences.

#### 1D. Customer dashboard

-   [ ] Add protected customer dashboard route/view.
-   [ ] Restore authenticated customer state on page refresh using the
    established session approach.
-   [ ] Fetch profile and preferences.
-   [ ] Show customer display name and a clear next action.
-   [ ] Show empty states for plans, favourites and shopping lists.
-   [ ] Provide profile/preferences edit entry point.
-   [ ] Add logout.
-   [ ] Redirect unauthenticated users to login.
-   [ ] Do not show admin controls or admin status to ordinary
    customers.
-   [ ] Verify mobile and desktop layouts.

**Phase 1 acceptance:** A real customer can register, verify email, log
in, complete onboarding, save preferences, refresh the browser and see
their persisted customer dashboard. Admin functionality is separate and
backend-restricted.

### Phase 2 --- Ingredient catalogue and recipe content foundation

**Goal:** Establish trusted structured food content before meal
generation.

#### 2A. Ingredient catalogue

-   [ ] Define ingredient creation/review workflow.
-   [ ] Define canonical ingredient names and aliases.
-   [ ] Define local/regional names and future Tamil translations.
-   [ ] Define ingredient categories.
-   [ ] Define allergen relationships.
-   [ ] Define raw/cooked states and edible portion fields.
-   [ ] Define compatible units and conversion rules.
-   [ ] Add duplicate detection and canonical matching.
-   [ ] Add source/provenance fields for nutrition data.
-   [ ] Import a small reviewed ingredient seed set.
-   [ ] Validate ingredient references and publication state.
-   [ ] Test search, aliases, allergens and state distinctions.

#### 2B. Recipe content

-   [ ] Finalize recipe editorial guidelines.
-   [ ] Define beginner-friendly instruction standards.
-   [ ] Define portion and serving conventions.
-   [ ] Define meal categories and cuisine taxonomy.
-   [ ] Define vegetarian/egg/non-vegetarian classification rules.
-   [ ] Define preparation time and active cooking time.
-   [ ] Define equipment requirements.
-   [ ] Define recipe source and licensing review.
-   [ ] Create recipe review checklist.
-   [ ] Build import workflow using existing Pydantic schema and
    transactional service.
-   [ ] Ensure import is idempotent or safely rejects conflicting
    immutable versions.
-   [ ] Keep imported content draft until reviewed.
-   [ ] Ensure no illustrative fixtures are published.

#### 2C. Initial recipe collection

Initial planning target: 100 reviewed recipes, not a claim that these
already exist.

Planning allocation: - Tamil Nadu: 35. - Kerala: 20. - Karnataka: 20. -
Andhra Pradesh/Telangana: 15. - Other familiar Indian dishes: 10.

Planning meal distribution: - Breakfast: 25. - Morning snack: 15. -
Lunch: 25. - Evening snack: 15. - Dinner: 20.

-   [ ] Confirm recipe selection and avoid over-concentrating on one
    cuisine.
-   [ ] Collect/author content with rights cleared.
-   [ ] Review ingredient quantities and serving size.
-   [ ] Review steps, timings and equipment.
-   [ ] Review allergens and dietary labels.
-   [ ] Review nutritional source/provenance.
-   [ ] Publish only approved recipes.
-   [ ] Add content QA report and recipe coverage metrics.

**Phase 2 acceptance:** The application has a reviewed, searchable
structured recipe collection with reliable ingredient/allergen
references and auditable nutrition provenance.

### Phase 3 --- Recipe discovery and cooking experience

**Goal:** Customers can find and confidently cook an appropriate recipe.

-   [ ] Create authenticated/public recipe list API according to product
    policy.
-   [ ] Add pagination and stable sorting.
-   [ ] Add search by recipe name and supported aliases.
-   [ ] Add filters for cuisine, meal category and diet.
-   [ ] Add safe filtering for customer allergies and exclusions.
-   [ ] Add recipe detail API.
-   [ ] Display ingredients with quantities and units.
-   [ ] Display serving count and serving adjustment behavior.
-   [ ] Display ordered cooking steps.
-   [ ] Display preparation/cooking time.
-   [ ] Display equipment.
-   [ ] Display allergen warnings.
-   [ ] Display nutrition only when supported by validated data.
-   [ ] Show when nutrition is incomplete.
-   [ ] Add beginner-friendly instruction layout.
-   [ ] Add responsive recipe cards and detail page.
-   [ ] Add loading, empty and error states.
-   [ ] Add recipe favourites API/UI.
-   [ ] Test that unpublished/draft recipes are not exposed to
    customers.
-   [ ] Test allergy filters and unauthorized access.

**Phase 3 acceptance:** A customer can search, filter, inspect and cook
an approved recipe on mobile and desktop.

### Phase 4 --- Deterministic meal-planning engine

**Goal:** Generate useful plans using verified constraints before adding
AI.

#### 4A. Formalize inputs and hard constraints

-   [ ] Define meal-plan request schema.
-   [ ] Define daily and weekly plan horizon.
-   [ ] Define five meal slots and required/optional slot behavior.
-   [ ] Define servings/household size.
-   [ ] Apply allergy exclusions as hard filters.
-   [ ] Apply diet preference as hard filter.
-   [ ] Apply ingredient dislikes according to user setting.
-   [ ] Apply strict time limit if the user marks it strict.
-   [ ] Apply equipment compatibility.
-   [ ] Exclude draft, archived or unapproved recipes.
-   [ ] Ensure all ingredients resolve to canonical ingredient records.
-   [ ] Ensure missing data does not become false certainty.

#### 4B. Candidate ranking

Initial tentative weights (must be validated through tests and user
feedback): - Cuisine match: 25%. - Budget fit: 25%. - Time fit: 20%. -
Ingredient availability/overlap: 15%. - Variety/history: 15%.

-   [ ] Keep hard filters separate from ranking scores.
-   [ ] Document scoring inputs and tie-breaking.
-   [ ] Avoid deterministic bias toward a tiny subset of recipes.
-   [ ] Add repeat limits across days and meal slots.
-   [ ] Add ingredient overlap/waste reduction where practical.
-   [ ] Add explainable selection reasons.
-   [ ] Add deterministic tests for ranking and tie-breaking.

#### 4C. Plan generation and validation

-   [ ] Generate one-day plan.
-   [ ] Generate seven-day plan.
-   [ ] Validate five meal slots per day.
-   [ ] Validate diet/allergen/equipment/time constraints.
-   [ ] Validate budget estimates.
-   [ ] Validate recipe publication/version state.
-   [ ] Validate servings and ingredient quantities.
-   [ ] Detect impossible combinations.
-   [ ] Return clear infeasibility explanation rather than silently
    violating constraints.
-   [ ] Persist plan and planned meals transactionally.
-   [ ] Record recipe versions used by a saved plan.
-   [ ] Add plan retrieval and history.
-   [ ] Test edge cases and property-based invariants where appropriate.

#### 4D. Customer experience

-   [ ] Add "Create daily plan".
-   [ ] Add "Create 7-day plan".
-   [ ] Show plan generation/loading state.
-   [ ] Show meals by day and slot.
-   [ ] Explain why a meal was selected.
-   [ ] Show estimated cost and uncertainty.
-   [ ] Show time and servings.
-   [ ] Allow plan review before replacing.
-   [ ] Add regenerate behavior with clear confirmation.
-   [ ] Preserve hard constraints on every regeneration.
-   [ ] Add empty and infeasible states.

**Phase 4 acceptance:** A customer can generate and retrieve a valid
daily and weekly plan; automated tests prove that hard constraints are
never violated.

### Phase 5 --- Shopping list and budget management

-   [ ] Define shopping list and item APIs.
-   [ ] Generate list from selected meal plan.
-   [ ] Aggregate quantities only when units are compatible.
-   [ ] Preserve ingredient state where relevant.
-   [ ] Avoid unsafe conversions.
-   [ ] Group by category.
-   [ ] Support checked/purchased status.
-   [ ] Support manual item addition/removal if approved.
-   [ ] Add price data model/source/date/location/confidence if not
    already sufficient.
-   [ ] Add cost calculation and unit normalization.
-   [ ] Distinguish estimated cost from live retail price.
-   [ ] Account for package sizes only when reliable data exists.
-   [ ] Display total and budget variance.
-   [ ] Add plan-to-shopping-list consistency tests.
-   [ ] Add mobile-friendly shopping checklist.

**Phase 5 acceptance:** A customer can convert a plan into a usable
shopping list and understand the quality/age of price estimates.

### Phase 6 --- Personalization and daily-use features

-   [ ] Replace one planned meal with another valid recipe.
-   [ ] Revalidate all hard constraints after replacement.
-   [ ] Save/unsave favourites.
-   [ ] View previous plans.
-   [ ] Regenerate one day without unintentionally changing other days.
-   [ ] Adjust serving count and recalculate quantities.
-   [ ] Record meal feedback (liked/disliked/cooked) with consent and
    clear purpose.
-   [ ] Use history to improve variety without creating filter bubbles.
-   [ ] Add pantry/available ingredients only after a clear data model
    and UX design.
-   [ ] Add leftovers and ingredient reuse only with explicit,
    understandable logic.
-   [ ] Add optional reminders only with user consent and notification
    preferences.

**Phase 6 acceptance:** Customers can use the app repeatedly, adjust
plans and receive relevant recommendations without violating
constraints.

### Phase 7 --- Admin content-management application

**Goal:** Build a separate, restricted operational panel for trusted
staff.

-   [ ] Decide admin deployment boundary: separate app/subdomain or
    isolated route/build.
-   [ ] Ensure public customer navigation has no admin setup entry.
-   [ ] Use existing admin membership table and `require_admin`.
-   [ ] Add admin login flow that uses existing identity provider.
-   [ ] Verify admin membership server-side for every admin endpoint.
-   [ ] Add secure first-admin bootstrap procedure documentation.
-   [ ] Remove any public-facing admin bootstrap UI from customer build.
-   [ ] Add admin dashboard shell.
-   [ ] Add ingredient management.
-   [ ] Add allergen and taxonomy management.
-   [ ] Add recipe create/edit/draft workflows.
-   [ ] Add recipe version review.
-   [ ] Add nutrition source/provenance review.
-   [ ] Add publish/unpublish workflow.
-   [ ] Add audit log for sensitive admin actions.
-   [ ] Add least-privilege roles only when role requirements are
    defined.
-   [ ] Add safe image/media upload and rights metadata.
-   [ ] Add admin tests for non-admin denial and cross-tenant/security
    boundaries.
-   [ ] Ensure admin endpoints do not trust frontend-only role flags.

**Phase 7 acceptance:** Authorized admins can manage reviewed content;
ordinary customers cannot access admin UI or APIs.

### Phase 8 --- Nutrition, safety and data governance

-   [ ] Confirm commercial rights for every nutrition dataset used.
-   [ ] Document data provenance and attribution obligations.
-   [ ] Validate per-100g versus per-serving units.
-   [ ] Validate edible portion and raw/cooked state.
-   [ ] Validate recipe yield and serving calculations.
-   [ ] Preserve missing nutrients as NULL.
-   [ ] Add source confidence and review status.
-   [ ] Establish nutrition review and correction process.
-   [ ] Establish allergen taxonomy and cross-contact disclaimer policy.
-   [ ] Add warnings for incomplete or unverified values.
-   [ ] Prevent unsupported health/therapeutic claims.
-   [ ] Establish content takedown and correction process.
-   [ ] Add auditability for data changes.

**Phase 8 acceptance:** Published nutritional and allergen data is
traceable, reviewed and presented without false precision or unsupported
health claims.

### Phase 9 --- Security, reliability and operational readiness

-   [ ] Threat model customer and admin authentication.
-   [ ] Review JWT verification and key rotation behavior.
-   [ ] Review token storage and session expiration.
-   [ ] Enforce rate limits on auth and expensive APIs.
-   [ ] Ensure correct 429 handling and retry guidance.
-   [ ] Add abuse protection to registration and password reset.
-   [ ] Review CORS and allowed origins.
-   [ ] Review RLS policies and backend ownership checks.
-   [ ] Review database privileges and connection pooling.
-   [ ] Review SQL injection and unsafe query patterns.
-   [ ] Review input validation and output encoding.
-   [ ] Review file upload limits and media handling.
-   [ ] Ensure logs never contain secrets or personal credentials.
-   [ ] Add structured logs with request correlation IDs.
-   [ ] Add uptime and error monitoring.
-   [ ] Add backups and verify restore procedures.
-   [ ] Define migration rollback/recovery process.
-   [ ] Add dependency and vulnerability review process.
-   [ ] Add automated CI for tests, lint and builds.
-   [ ] Add staging environment separate from production.
-   [ ] Add deployment approval and rollback procedure.
-   [ ] Define incident response and security contact.
-   [ ] Perform independent security review before public scale.

**Phase 9 acceptance:** The system has tested operational procedures,
appropriate security controls and observable failure handling.

### Phase 10 --- Performance, accessibility and launch

-   [ ] Define target user journeys and performance budgets.
-   [ ] Test mobile on common Android screen sizes.
-   [ ] Test desktop and tablet layouts.
-   [ ] Test keyboard navigation and visible focus.
-   [ ] Add accessible labels, headings and error announcements.
-   [ ] Check color contrast.
-   [ ] Optimize image formats/sizes and lazy loading.
-   [ ] Review bundle size and route-level loading.
-   [ ] Add API pagination and caching where safe.
-   [ ] Load-test meal generation and common read APIs.
-   [ ] Check database indexes using query evidence.
-   [ ] Test slow network and backend cold-start behavior.
-   [ ] Test email delivery and password recovery.
-   [ ] Test backup restoration.
-   [ ] Run end-to-end regression suite.
-   [ ] Create customer help/FAQ and privacy/terms pages.
-   [ ] Publish support and contact process.
-   [ ] Set up production domain and TLS.
-   [ ] Configure production SMTP and sender authentication
    (SPF/DKIM/DMARC as applicable).
-   [ ] Set up analytics with privacy-conscious event collection.
-   [ ] Define beta cohort and feedback process.
-   [ ] Run closed beta.
-   [ ] Fix launch-blocking issues.
-   [ ] Run go/no-go review.
-   [ ] Launch gradually and monitor.

**Phase 10 acceptance:** A production release has passed functional,
security, accessibility, performance and operational launch checks.

### Phase 11 --- Post-launch product growth

-   [ ] Monitor activation, onboarding completion and plan generation
    success.
-   [ ] Monitor recipe views, cooking feedback and plan retention.
-   [ ] Track errors and performance without collecting unnecessary
    personal data.
-   [ ] Establish support and bug triage.
-   [ ] Prioritize based on observed customer problems.
-   [ ] Add Tamil translations and localized terminology.
-   [ ] Expand recipes to more Indian regions.
-   [ ] Add local/seasonal ingredient price coverage where trustworthy.
-   [ ] Improve household and serving support.
-   [ ] Improve ingredient substitutions using reviewed compatibility
    data.
-   [ ] Add pantry and leftover workflows if validated by demand.
-   [ ] Add reminders with opt-in controls.
-   [ ] Review monetization only after core customer value is
    demonstrated.

**Phase 11 acceptance:** Product improvements are driven by measured
user value, safety and reliability.

### Phase 12 --- Enterprise readiness and scale

This phase is not part of the MVP. Start only when the product has
proven demand and operational maturity.

#### Enterprise identity and access

-   [ ] Define organization/tenant model only if B2B use cases are
    approved.
-   [ ] Define organization membership and invitations.
-   [ ] Define roles and permissions with least privilege.
-   [ ] Add SSO/SAML/OIDC only when required by target customers.
-   [ ] Add MFA policy for privileged roles.
-   [ ] Add access review and offboarding workflow.
-   [ ] Add tenant isolation tests.

#### Enterprise data governance

-   [ ] Define data classification and retention policy.
-   [ ] Define data export and deletion workflows.
-   [ ] Define audit log retention and access.
-   [ ] Define encryption and key management requirements.
-   [ ] Define data residency needs by customer/market.
-   [ ] Define vendor and subprocessors inventory.
-   [ ] Define data processing agreements where applicable.
-   [ ] Establish privacy impact assessment process.

#### Enterprise operations

-   [ ] Define service-level objectives (SLOs).
-   [ ] Define support tiers and escalation.
-   [ ] Define incident response and postmortems.
-   [ ] Define disaster recovery objectives (RPO/RTO).
-   [ ] Test backup and disaster recovery regularly.
-   [ ] Add capacity planning and load testing.
-   [ ] Add multi-environment release governance.
-   [ ] Add feature flags and controlled rollout.
-   [ ] Add observability dashboards and alert ownership.
-   [ ] Define business continuity process.

#### Enterprise integrations and commercial readiness

-   [ ] Identify validated enterprise use cases before adding
    integrations.
-   [ ] Define stable public/private API contracts and versioning.
-   [ ] Add API keys/service accounts only with scoped permissions and
    rotation.
-   [ ] Evaluate grocery, HR/wellness or partner integrations only after
    legal/security review.
-   [ ] Define enterprise billing, invoicing and support model if
    commercial strategy requires it.
-   [ ] Define contractual, privacy and compliance requirements for each
    market.
-   [ ] Complete independent penetration testing and remediation.
-   [ ] Obtain certifications only when commercially justified and
    properly audited; never claim certification prematurely.

**Phase 12 acceptance:** Enterprise controls are implemented and
independently validated against actual customer, legal and contractual
requirements. Enterprise readiness must not be claimed from feature
presence alone.

------------------------------------------------------------------------

## 6. Current checkpoint register

This section is the operational status summary. Update it after every
task. Detailed acceptance criteria live in the phase sections above.

  -------------------------------------------------------------------------------------------
  ID                Checkpoint            Status            Evidence / notes
  ----------------- --------------------- ----------------- ---------------------------------
  P0                Project foundation,   IN PROGRESS       Foundation code, migrations and
                    backend, database and                   tests exist; live migration and
                    test deployment                         Render deployment state are not
                                                            verified locally

  P0-AUTH           Supabase Auth         COMPLETE          Safe diagnostic logging
                    diagnostics                             committed; commit `f95cdc32`;
                                                            logs identified Supabase
                                                            `429 email rate limit exceeded`

  P0-SMTP           Custom SMTP and       IN PROGRESS       Supabase logs show signup 200
                    end-to-end email                        with confirmation requested and
                    verification                            the email limiter changed to
                                                            30/hour; verification still needs
                                                            a fresh, successfully opened link

  P0-429            Preserve provider     COMPLETE          Provider HTTP 429 now maps to
                    HTTP 429 response to                    a sanitized client-facing rate
                    client                                  limit response; focused and full
                                                            backend tests pass

  P1-UI             Customer auth UI and  COMPLETE          `App.tsx`, `CustomerAuth.tsx`;
                    remove admin entry                      frontend lint/build passed;
                    from public                             no frontend test runner exists
                    navigation
                    from public
                    navigation

  P1-PREF           Persist onboarding    BLOCKED           Backend profile/preferences APIs
                    profile/preferences                     exist and backend tests pass, but
                                                            onboarding has no display-name
                                                            field or verified UUID mapping for
                                                            allergies, disliked ingredients and
                                                            equipment; do not invent IDs or drop
                                                            safety restrictions

  P1-DASH           Protected customer    NOT STARTED       Depends on P1-PREF
                    dashboard

  P1-ADMIN-SEP      Separate              IN PROGRESS       Admin setup removed from public
                    administrator                           navigation; dedicated admin
                    interface boundary                      app/route boundary still to be
                                                            completed

  P2                Ingredient catalogue  NOT STARTED       Depends on data
                    and reviewed recipes                    governance/licensing

  P3                Recipe discovery and  NOT STARTED       Depends on approved recipe data
                    cooking UI

  P4                Deterministic         NOT STARTED       Core differentiator
                    daily/weekly meal
                    engine

  P5                Shopping list and     NOT STARTED       Depends on meal plan and price
                    budget                                  data

  P6                Personalization and   NOT STARTED       Depends on saved plans and
                    convenience                             feedback

  P7                Separate admin        NOT STARTED       Backend admin
                    content-management                      authorization/bootstrap already
                    app                                     exists

  P8                Nutrition and data    IN PROGRESS       Schema/validators exist; dataset
                    governance                              licensing and content review
                                                            remain

  P9                Security and          NOT STARTED       Existing foundations; full review
                    operational readiness                   outstanding

  P10               Production launch     NOT STARTED       Current Render deployment is
                                                            test/staging

  P11               Post-launch growth    NOT STARTED       After launch

  P12               Enterprise readiness  NOT STARTED       Only after product-market and
                                                            operational validation
  -------------------------------------------------------------------------------------------

------------------------------------------------------------------------

## 7. Current position --- update this after each task

**Current phase:** Phase 1 --- Customer application foundation\
**Last completed implementation task:** Fix confirmation-pending signup response
handling while preserving retryable profile creation\
**Last verified checks:** Focused authentication tests passed 29 tests; full
backend `pytest` passed 97 tests with 3 existing deprecation warnings. The
signup parser now accepts a valid user ID with both tokens absent as
confirmation-pending, including responses without confirmation timestamp
fields, while rejecting missing IDs, malformed tokens and incomplete sessions.\
**Next recommended task:** Send one real customer registration test email and
verify delivery and confirmation behavior (P0-SMTP).\
**Current known blockers:** Supabase signup now completes with confirmation
requested and the configured email limit is 30/hour. A short per-address
cooldown can still return 429, and one verification attempt returned `403`
because the one-time token was not found; test with a fresh link only once.
Customer
onboarding persistence also lacks a safe display-name field and verified
catalog UUID mapping for structured restrictions and equipment.\
**Admin separation:** Admin setup is removed from public navigation;
separate restricted admin interface still needs a deliberate
implementation.\
**Deployment status:** Render frontend/backend test deployments exist;
verify current live commit/status before relying on them.\
**Last updated:** 31 October 2026.

------------------------------------------------------------------------

## 8. Rules for deciding what to do next

Codex must use this priority order:

1.  Resolve a blocker preventing the current phase from being tested.
2.  Finish the earliest incomplete checkpoint whose dependencies are
    met.
3.  Do not start a later phase while an earlier dependency is
    incomplete.
4.  Prefer customer-critical MVP work over optional admin convenience or
    advanced AI.
5.  Keep admin security separate and enforce it server-side.
6.  Do not add AI meal generation until deterministic rules and verified
    recipe data are ready.
7.  Do not add enterprise features before MVP validation.
8.  If a task requires product, legal, licensing, cost or security
    decisions, present the decision and wait for approval.
9.  Do not invent a completion status. Ask for evidence or run the
    relevant check.
10. When the user says "continue", resume from the
    `Next recommended task` and current checkpoint register.

------------------------------------------------------------------------

## 9. Codex task response format

Use this concise format after each task:

**Checkpoint:** `P1-PREF — Persist onboarding profile/preferences`\
**Result:** Complete / Partial / Blocked\
**Changed files:** List only\
**Checks:** Exact commands and pass/fail results\
**Acceptance:** Which criteria were verified\
**Remaining issues:** Only real blockers\
**Master plan:** Updated / Not updated (explain if not)\
**Next checkpoint:** One next action

Do not include long progress narration, repeat the whole plan, or claim
external deployment success without verification.

------------------------------------------------------------------------

## 10. Non-negotiable safety and quality rules

-   Never store passwords in application tables.
-   Never trust client-provided user IDs or admin roles.
-   Never let a customer promote themselves to admin.
-   Never expose admin bootstrap in the public customer experience.
-   Never log secrets, tokens, passwords, full auth headers or raw
    sensitive request bodies.
-   Never weaken RLS or remove ownership checks to make a test pass.
-   Never bypass allergy restrictions to fill a meal slot.
-   Never invent nutrition values or convert missing values to zero.
-   Never publish unreviewed illustrative recipe data.
-   Never use unlicensed recipe text or images.
-   Never claim exact food prices without trustworthy current data.
-   Never present the product as providing medical diagnosis or
    therapeutic diets.
-   Never run destructive migrations or database resets without explicit
    approval and a recovery plan.
-   Never deploy untested breaking changes directly to production.
-   Never claim enterprise, security or compliance certification without
    independent evidence.

**End of living project instructions.**
