# MealMate India MVP Product Requirements

## 1. Target users and problems

MealMate is for Indian students and working professionals who:

- Struggle to decide what to cook each day.
- Have limited time, cooking experience, equipment, or budget.
- Need practical South Indian meal ideas rather than generic recipes.
- Want ingredient quantities, simple steps, and a consolidated shopping list.
- Need food preferences and allergy restrictions respected consistently.

## 2. Core product value

MealMate turns a user’s food preferences, restrictions, budget, time, skill level, equipment, and cuisine preference into practical daily or 7-day Indian meal plans. It reduces decision-making while making cooking and shopping easier to follow.

## 3. User journeys

### Discovery

1. User opens the responsive landing page.
2. User understands the product value and sees a sample plan preview.
3. User selects **Plan my meals** to begin onboarding.

### Registration

1. User chooses sign up or sign in.
2. User completes authentication.
3. User returns to onboarding or their saved plan.

### Onboarding

1. User selects vegetarian, egg, or non-vegetarian preference.
2. User enters allergies and disliked ingredients.
3. User enters a daily food budget.
4. User selects cooking skill, available time, equipment, and preferred cuisine.
5. User reviews and submits preferences.

### Meal planning

1. User requests a daily or 7-day plan.
2. MealMate generates breakfast, morning snack, lunch, evening snack, and dinner suggestions.
3. User sees applicable preparation time, cooking time, nutrition, and budget information.
4. User can open a recipe, regenerate an unsuitable suggestion, or adjust preferences.

### Recipe viewing

1. User opens a planned or discovered recipe.
2. User sees servings, ingredient quantities, preparation/cooking times, steps, nutrition, and allergen information.
3. User can save or remove the recipe from favourites.

### Shopping list

1. User generates a list from a daily or weekly plan.
2. MealMate combines repeated ingredients and preserves quantities and units.
3. User views, checks off, and updates the list.

## 4. Functional requirements

- Provide responsive English-language landing, onboarding, plan, recipe, favourites, and shopping-list views.
- Support daily and 7-day meal plans with five defined meal slots.
- Store and apply food preference, allergy, disliked-ingredient, budget, skill, time, equipment, and cuisine inputs.
- Start with a verified South Indian recipe catalogue.
- Display recipe ingredients, quantities, servings, preparation time, cooking time, instructions, nutrition, and allergens.
- Allow authenticated users to save preferences, favourites, meal plans, and shopping lists.
- Allow users to regenerate or replace an unsuitable planned meal.
- Show useful validation, loading, empty, no-match, and error states.
- Keep user data isolated and prevent unauthorised access.

## 5. Nutrition and allergy safety rules

- Publish only recipe, ingredient, allergen, and nutrition data from documented, verified sources.
- Show nutrition values with their serving context; never estimate or invent missing values.
- Treat allergy and disliked-ingredient inputs as exclusion rules, not optional display preferences.
- Enforce restrictions in backend meal-plan generation and recipe access; frontend checks are not sufficient.
- If safe matching recipes are unavailable, show a clear no-match message and request a preference change.
- Do not make medical, treatment, prevention, or disease-related diet claims.
- Tell users that nutrition information is an estimate where the verified source identifies it as such.

## 6. MVP versus future features

### MVP

- English responsive website.
- South Indian recipes.
- Vegetarian, egg, and non-vegetarian preferences.
- Daily and 7-day plans with five meal slots.
- Onboarding preferences and authenticated user accounts.
- Verified recipe, ingredient, allergen, and nutrition data.
- Budget, time, skill, equipment, and preference-aware rule-based planning.
- Recipe details, favourites, and generated shopping lists.

### Future

- Additional Indian cuisines and regional adaptations.
- Tamil and other language support.
- Nutritionist-reviewed or advanced nutrition goals, if appropriately governed.
- Pantry tracking, ingredient substitutions, price integrations, reminders, meal history, and household planning.
- More advanced recommendation and personalisation models after sufficient trusted data exists.

## 7. Acceptance criteria

### Landing and discovery

- A new user can understand the product purpose and start onboarding from the landing page on mobile and desktop.

### Registration

- A user can create an account, sign in, sign out, and return to their saved MealMate state with appropriate error feedback.

### Onboarding

- Required selections cannot be skipped, optional allergy/dislike details can be left blank, progress is visible, and submitted answers are saved to the authenticated user.

### Meal planning

- A user can request daily and 7-day plans containing all five meal slots, and every suggestion respects stored restrictions or returns a clear no-match state.

### Recipe viewing

- Every published recipe displays complete verified ingredients, quantities, steps, timings, serving context, nutrition source context, and allergen information.

### Favourites

- An authenticated user can add, view, and remove favourites, and cannot access another user’s favourites.

### Shopping lists

- A user can generate a list from a plan, see combined ingredient quantities and units, check items off, and retain the list for later viewing.

### Safety and quality

- Backend validation and authorisation tests pass; restricted recipes are excluded; no unverified nutrition or medical claims appear in the MVP.
