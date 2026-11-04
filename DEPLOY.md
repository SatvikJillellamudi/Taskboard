# Deploying Taskboard (free)

Three pieces, all free:
- **Neon**: the PostgreSQL database (the free plan doesn't expire)
- **Render**: the FastAPI backend (web service) and the React frontend (static site)

Allow about 30 minutes the first time.

## 1. Push the latest code
Render deploys from GitHub, so `render.yaml` must be in your repo.
```bash
cd ~/taskboard
git add .
git status
git commit -m "Postgres, migrations, production config, deploy setup"
git push
```

## 2. Create the database on Neon
1. Sign up at neon.com (signing in with GitHub is quickest).
2. Create a project named `taskboard`. Pick the region closest to you (for example AWS US East).
3. Open the project's **Connect** dialog. **Turn connection pooling off**, so you get the
   direct connection string (the app manages its own connection pool).
4. Copy the connection string. It looks like:
   `postgresql://neondb_owner:XXXX@ep-something.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require`

Treat it like a password: never commit it or paste it publicly.

## 3. Deploy both services on Render
1. Sign up at render.com with your GitHub account.
2. Click **New**, then **Blueprint**, and pick your `taskboard` repo. Render reads `render.yaml`
   and shows two services: `taskboard-api` and `taskboard-web`.
3. It asks for three values. Render URLs follow the pattern `https://<service-name>.onrender.com`:
   | Variable | Value |
   |---|---|
   | `DATABASE_URL` | your Neon connection string |
   | `CORS_ORIGINS` | `https://taskboard-web.onrender.com` |
   | `VITE_API_URL` | `https://taskboard-api.onrender.com` |

   Use `https`, and no trailing slash on `CORS_ORIGINS`. `JWT_SECRET` is generated for you.
4. Click **Apply** and wait for both deploys to finish (a few minutes).

## 4. Check the real URLs
If a service name was already taken, Render adds a suffix, such as `taskboard-api-x7k2.onrender.com`.
Open each service in the dashboard and compare its URL to what you entered.

If either differs:
- **API's real URL differs** → open `taskboard-web` → **Environment** → fix `VITE_API_URL` → save.
  Then **Manual Deploy → Deploy latest commit**. The frontend reads this value at build time,
  so it needs a rebuild.
- **Frontend's real URL differs** → open `taskboard-api` → **Environment** → fix `CORS_ORIGINS`
  → save (it redeploys automatically).

## 5. Verify it works
1. Visit `https://<your-api>/health`. You should see `{"status":"ok"}`. The first visit can
   take about a minute while the free server wakes up.
2. Visit `https://<your-api>/docs` for the interactive API docs.
3. Open the frontend URL, sign up, and create a board.
4. Real-time check: open the board in a second window (or share it with a second account in
   an incognito window) and move a card. It should move in both.

## Troubleshooting
| Symptom | Likely cause and fix |
|---|---|
| Login fails with "Failed to fetch" | `CORS_ORIGINS` doesn't exactly match the frontend URL (check `https`, no trailing slash), or `VITE_API_URL` is wrong. Open the browser dev tools (F12) → Console: a CORS error confirms it. |
| API deploy fails: "Unsafe production config" | `DATABASE_URL` is missing or isn't the Neon string. Fix it under Environment. |
| API deploy fails during `alembic upgrade` | The database URL is wrong or Neon is unreachable. Check the API service's **Logs** tab. |
| Refreshing a board page shows "Not Found" | The rewrite rule didn't apply. Check `taskboard-web` → **Redirects/Rewrites** for `/*` → `/index.html` (rewrite). |
| Board says "Reconnecting…" forever | `VITE_API_URL` must start with `https://` so the live connection uses secure `wss://`. |
| Anything else | The **Logs** tab on each Render service shows the real error. |

## What the free tier means
- The API **sleeps after 15 idle minutes** and takes about a minute to wake. The app shows a
  "waking up the server" notice so this doesn't look broken.
- Render gives 750 free instance hours a month: enough for one always-available service.
- Neon's free plan gives 0.5 GB of storage, far more than this app needs.

## Afterward
Add the live URL to the top of `README.md` (replace the placeholder) and to your resume.
