# 🚀 Render Deployment Guide (Permanent URLs)

This guide will help you move your SOC platform from temporary "Cloudflare Tunnels" to permanent, enterprise-grade URLs on Render.

## 📋 Prerequisites
- A GitHub account.
- A Render account ([render.com](https://render.com)).
- Your project uploaded to a GitHub repository.

---

## 🏗️ Step 1: Prepare the Code for Render
Render needs to know how to start your application.

### 1. Requirements File
Ensure `requirements.txt` is updated. You also need a production server like `gunicorn`.
```text
gunicorn
# ... (existing requirements)
```

### 2. Procfile (Optional but recommended)
Create a file named `Procfile` in your root directory:
- For Director: `web: gunicorn parent_app:app`
- For Client: `web: gunicorn app:app`

---

## 🌐 Step 2: Deploy the Director Dashboard (Permanent)

1. **New Web Service**: In Render, click **New +** > **Web Service**.
2. **Connect Repo**: Select your GitHub repository.
3. **Configuration**:
   - **Name**: `ccl-guard-director`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn parent_app:app`
4. **Environment Variables**:
   - `PORT`: `5005`
   - `DIRECTOR_PASSWORD`: *[Your Secret Password]*
5. **Persistence (Crucial)**:
   - Go to the **Disk** tab.
   - Click **Add Disk**.
   - **Name**: `director-db`
   - **Mount Path**: `/data`
   - **Size**: 1GB (Free tier)
   - *Update `parent_database.py` to point to `/data/parent_soc.db`.*

**Result**: Your Director is now live at `https://ccl-guard-director.onrender.com`.

---

## 🛡️ Step 3: Deploy the Client Dashboard (Permanent)

Follow the same steps as the Director, but with these changes:

1. **Configuration**:
   - **Name**: `ccl-guard-[client-name]`
   - **Start Command**: `gunicorn app:app`
2. **Environment Variables**:
   - `PORT`: `5001`
   - `PARENT_SERVER_URL`: `https://ccl-guard-director.onrender.com`
3. **Persistence**:
   - Add a Disk mounted at `/data`.
   - *Update `database.py` to point to `/data/soc.db`.*

**Result**: Your client is now live at `https://ccl-guard-client.onrender.com`.

---

## 🛡️ Benefits of this approach:
- **Zero Maintenance**: No need to keep a PC running or restart Cloudflare tunnels.
- **Auto-Scale**: Handles more traffic automatically.
- **SSL Included**: Automatic HTTPS (locked green padlock).
- **Permanent**: The URL never changes, even if the server restarts.
