# Deploy CardeTrade on Render (Free)

## Prerequisites

- A [Render](https://render.com) account (free tier)
- Your code pushed to a GitHub/GitLab repository

## Steps

### 1. Create a `requirements.txt`

Already provided. Render will auto-install from it.

### 2. Create a `render.yaml` (optional but recommended)

```yaml
services:
  - type: web
    name: cardetrade
    env: python
    buildCommand: pip install -r requirements.txt && python manage.py migrate
    startCommand: gunicorn cardetrade.wsgi:application --bind 0.0.0.0:$PORT
    envVars:
      - key: DJANGO_SECRET_KEY
        generateValue: true
      - key: DJANGO_DEBUG
        value: False
      - key: ALLOWED_HOSTS
        value: .onrender.com
      - key: PYTHON_VERSION
        value: 3.11.5
```

### 3. Manual Deploy (via Dashboard)

1. Push code to GitHub
2. Log in to [Render Dashboard](https://dashboard.render.com)
3. Click **New +** → **Web Service**
4. Connect your GitHub repo
5. Fill in:

| Field | Value |
|-------|-------|
| Name | `cardetrade` |
| Runtime | `Python 3` |
| Build Command | `pip install -r requirements.txt && python manage.py migrate` |
| Start Command | `gunicorn cardetrade.wsgi:application --bind 0.0.0.0:$PORT` |
| Plan | **Free** |

6. Add environment variables:

| Key | Value |
|-----|-------|
| `DJANGO_SECRET_KEY` | Generate a long random string |
| `DJANGO_DEBUG` | `False` |
| `ALLOWED_HOSTS` | `.onrender.com,cardetrade.onrender.com` |
| `PYTHON_VERSION` | `3.11.5` |

7. Click **Create Web Service**

### 4. Database

Render Free uses SQLite (stored ephemerally). For production, upgrade to **PostgreSQL**:

1. In Render dashboard: **New +** → **PostgreSQL**
2. Copy the `DATABASE_URL` internal connection string
3. Add to environment variables: `DATABASE_URL=postgres://...`

Then update `settings.py` to use `dj-database-url`:

```python
import dj_database_url
DATABASES['default'] = dj_database_url.config(default='sqlite:///db.sqlite3')
```

Add to requirements.txt: `dj-database-url`

### 5. Static & Media Files

For Render free tier, static files work with `whitenoise` (already configured if using default Django). For media uploads, use **Cloudinary** or **AWS S3** as Render's ephemeral storage will not persist uploads.

### 6. Create Admin

After deploy, run via Render Shell:

```bash
python manage.py createsuperuser
```

Or use the seed migration (already applied) — default admin: `admin@cardetrade.in` / `admin123`

### 7. Custom Domain (Optional)

- Free tier: `https://cardetrade.onrender.com`
- Custom: Render Dashboard → Settings → Custom Domain

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError` | Check `requirements.txt` includes all deps |
| Database errors | Run `python manage.py migrate` in Render Shell |
| 500 error | Check logs: Render Dashboard → Events → Logs |
| Static files 404 | Ensure `whitenoise` is in middleware and `STATIC_ROOT` is set |
