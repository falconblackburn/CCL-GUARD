# 🚀 Vercel 1-Click Deployment Guide

This guide provides the most accurate steps to deploy the CCL-Guard SOC Platform on Vercel for demonstrations.

## 1. Import Repository
1. Log in to [Vercel](https://vercel.com).
2. Click **Add New** -> **Project**.
3. Import your GitHub repository (`CCL-GUARD`).

## 2. Configure Framework & Settings
- **Framework Preset:** Select **Flask** (Vercel will detect the `vercel.json` I've optimized).
- **Root Directory:** Keep as `./` (Default).
- **Build Command:** (Leave Blank)
- **Output Directory:** (Leave Blank)

## 3. Mandatory Environment Variables
Add these in the **Environment Variables** section of your Vercel project:

| Variable | Value | Purpose |
| :--- | :--- | :--- |
| `VERCEL` | `1` | Enables serverless optimization & memory DB fallback. |
| `FLASK_SECRET_KEY` | `any-random-string` | Secures your session. |
| `GEMINI_API_KEY` | `your-google-ai-key` | Required for AI Remediation. |
| `DATABASE_URL` | `postgres://...` | **(Optional for Demo)** Required for persistent data. If missing, app uses Memory mode. |

## 4. Deployment Check
- **Client URL:** `https://your-app.vercel.app/`
- **Director URL:** `https://your-app.vercel.app/director/`

---

## 💡 Troubleshooting "Function Crashed"
If you still see a 500 error:
1. **Logs:** Check the Vercel **Logs** tab for specific Python tracebacks.
2. **Database:** If you aren't seeing any data, it's because the app is in **Memory Mode**. Connect a Vercel Postgres database to persist logs.
3. **Region:** Ensure your deployment region matches your database region for lowest latency.

---
*Created by Antigravity for CCL-Guard SOC.*
