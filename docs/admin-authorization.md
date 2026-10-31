# Administrator authorization

MealMate uses a server-managed allowlist in `admin_users`. The table is keyed
by the Supabase Auth user UUID and has RLS enabled without user-facing
policies. There is no public admin-registration endpoint. The first
administrator can use the protected `POST /api/v1/admin/bootstrap` endpoint;
it accepts no request body and requires a valid JWT, a confirmed email and the
configured bootstrap email.

## Adding the first administrator

1. Create or confirm the user in the Supabase Auth dashboard.
2. Copy the user UUID from the trusted Supabase dashboard; do not accept it
   from the user or a frontend request.
3. Apply the approved Alembic migrations using the trusted database operator
   path. The application must not auto-promote users.
4. Set the server-only `ADMIN_BOOTSTRAP_EMAIL` to the same address and restart
   the backend. Never expose this setting to the frontend.
5. Sign in as that confirmed user and call the protected bootstrap endpoint
   without a request body. The backend compares the provider-confirmed email,
   verifies the JWT subject, and atomically inserts the first administrator.

For controlled recovery, after applying the approved Alembic migrations, a
trusted database administrator may insert only that UUID directly:

   ```sql
   INSERT INTO public.admin_users (user_id)
   VALUES ('<SUPABASE_AUTH_USER_UUID>');
   ```

6. Verify the administrator through a protected backend operation. Never put
   the UUID, database credentials or service-role key in frontend code,
   logs or API responses.

Removing an administrator is the same controlled database operation using the
trusted operator path. Future recipe-import and publication routes must use
the backend `require_admin` dependency; ordinary authenticated users must
receive HTTP 403.
