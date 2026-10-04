# NaviGo — Replit & Cloud Deployment Guide

This guide covers deploying NaviGo to **Replit** (Autoscale or Reserved VM), **Render**, **Railway**, and **Fly.io**, ensuring 100% environment parity between local development and cloud production.

---

## 1. Quick Replit Deployment (Under 10 Minutes)

### Step 1: Import Repository
1. Log in to [Replit](https://replit.com/).
2. Click **Create Repl** → **Import from GitHub**.
3. Paste your repository URL and choose **Python** as the template.

### Step 2: Configure Workspace Secrets (Local Repl Environment)
In the left sidebar, click **Tools** → **Secrets** (Environment Variables) and add:

| Key | Description | Example Value |
|---|---|---|
| `APP_ENV` | Environment mode | `prod` |
| `PORT` | Bind port (Replit sets this automatically or default 8000) | `8000` |
| `PUBLIC_BASE_URL` | Your public Replit domain | `https://navigo.<your-username>.replit.app` |
| `ALLOWED_ORIGINS` | Comma-separated CORS allowed origins | `https://navigo.<your-username>.replit.app` |
| `CRON_SECRET` | Secret token for automated weather alert endpoint | `your_secure_cron_token_here` |
| `SUPABASE_URL` | *(Optional for Demo Mode)* Supabase Project URL | `https://xyz.supabase.co` |
| `SUPABASE_ANON_KEY` | *(Optional for Demo Mode)* Public Anon Key | `eyJ...` |
| `GEMINI_API_KEY` | *(Optional for Demo Mode)* Google AI Studio Key | `AIzaSy...` |
| `GEMINI_MODEL` | AI model version | `gemini-2.5-flash` |

> [!NOTE]
> If `SUPABASE_URL` and `GEMINI_API_KEY` are left empty, NaviGo automatically runs in **Zero-Dependency Demo Mode** using seeded local data and deterministic AI helpers.

### Step 3: Run & Verify in Webview
1. Click the **Run** button at the top.
2. Confirm the Webview opens and displays NaviGo with the interactive Leaflet map, destinations, and trip planner.
3. Check the console logs: startup should take under 2 seconds.

### Step 4: Configure Production Deployment (Autoscale / Reserved VM)
1. In the upper-right corner of Replit, click **Deploy**.
2. Select **Autoscale** (serverless scaling) or **Reserved VM** (always-on).
3. Verify the deployment settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `python run.py` *(Automatically handles auto-seeding, 0.0.0.0 binding, and disables reload in prod)*.
4. Add the same secrets into the **Deployment Secrets** tab.
5. Click **Deploy**. Your app will go live at `https://<your-repl-name>.replit.app`.

---

## 2. Post-Deployment Verification (Smoke Test)

Run the automated smoke test script against your live URL:

```bash
python scripts/smoke_test.py https://<your-repl-name>.replit.app
```

The script verifies:
- `GET /` (Frontend HTML)
- `GET /api/health`
- `GET /api/config`
- `GET /api/destinations` & `GET /api/destinations/naran`
- `GET /api/weather/hunza` (Open-Meteo live forecast)
- `GET /api/places` & `GET /api/places/nearby`
- `POST /api/trips/plan` (SSE stream)
- `POST /api/chat` (Grounded chatbot)
- `POST /api/vision/road` (Multipart photo analysis)
- `GET /api/alerts` & `GET /api/businesses`

---

## 3. Scheduled Weather Alerts in Cloud (Cron)

Because Replit Autoscale instances sleep when idle, in-process timers are not persistent. We implement weather checks via an authenticated HTTP endpoint:

- **Endpoint**: `POST /api/internal/cron/weather-alerts`
- **Header**: `Authorization: Bearer <CRON_SECRET>`

### Trigger Options:
1. **Replit Scheduled Deployment**: Set up a recurring trigger hitting the script `python scripts/cron_weather_alerts.py`.
2. **External Pinger (Cron-Job.org / UptimeRobot / GitHub Actions)**:
   - Schedule an HTTP POST to `https://<your-app>.replit.app/api/internal/cron/weather-alerts` every 30 minutes with the `Authorization` header.

---

## 4. Testing Hardware Features on Phone (Mic, Camera, GPS)

Microphone, camera, and geolocation require a secure HTTPS context. To test on a physical smartphone during local development:

1. **Option A: Cloudflare Tunnel (Quickest & Free)**:
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```
   Open the generated `https://xxxx.trycloudflare.com` link on your mobile browser.
2. **Option B: ngrok**:
   ```bash
   ngrok http 8000
   ```

---

## 5. Troubleshooting Table

| Issue | Cause | Fix |
|---|---|---|
| **Port Binding Error / 502 Bad Gateway** | Hard-coded `localhost` or wrong port | Ensure `main.py` binds to `0.0.0.0` and reads `PORT` from `os.environ`. |
| **Microphone / Geolocation Denied** | Insecure HTTP context | Must access via `localhost` or HTTPS domain (Replit or Cloudflare tunnel). |
| **SSE Stream Dropped (Loading Steps Freeze)** | Proxy buffering | NaviGo includes `X-Accel-Buffering: no` and 15s heartbeats `: heartbeat\n\n`. |
| **CORS Error in Browser** | `ALLOWED_ORIGINS` does not match domain | Add your production `https://*.replit.app` URL to `ALLOWED_ORIGINS`. |
| **Pillow Build Error** | Missing system headers | We use pure-Python prebuilt wheels `pillow==11.3.0` which install cleanly. |
| **Data Reset on Autoscale Restart** | Demo SQLite is on ephemeral container disk | In production, configure `SUPABASE_URL` and `SUPABASE_ANON_KEY` for permanent Postgres storage. |
| **Rollback Previous Release** | Deployment issue | In Replit Deployments tab, select the previous successful build and click "Promote to Production". |
