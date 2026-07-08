# Setup Guide — CardeTrade

## Prerequisites

- Python 3.11+
- pip
- Virtual environment (recommended)

## Step-by-Step

```bash
# 1. Clone
git clone <repo-url>
cd CardeTrade

# 2. Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
# Copy .env.example to .env and update SECRET_KEY
# Or use default dev settings

# 5. Run migrations
python manage.py makemigrations
python manage.py migrate

# 6. Create admin user
python manage.py createsuperuser

# 7. Run development server
python manage.py runserver
```

Visit `http://127.0.0.1:8000/app/`

## Default Admin Login

```
Username: admin
Password: admin123
```

(Create via createsuperuser or load fixture)

## Common Commands

| Command | Purpose |
|---------|---------|
| `python manage.py runserver` | Start dev server on port 8000 |
| `python manage.py check` | Validate project without running server |
| `python manage.py makemigrations` | Create new migrations |
| `python manage.py migrate` | Apply pending migrations |
| `python manage.py createsuperuser` | Create admin user |
| `python manage.py test` | Run all tests |
| `python manage.py test app.tests.TestClass.test_method` | Run specific test |

## Production Notes

- Set `DJANGO_DEBUG=False` in environment
- Use PostgreSQL instead of SQLite
- Configure `ALLOWED_HOSTS`
- Set strong `DJANGO_SECRET_KEY`
- Run `python manage.py collectstatic`
- Use Gunicorn + Nginx for serving

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `AUTH_USER_MODEL` error | Ensure `cardetrade/settings.py` has `AUTH_USER_MODEL = 'app.User'` |
| Migration conflicts | Delete `db.sqlite3` and migration files, re-run `makemigrations` + `migrate` |
| Static files not loading | Run `python manage.py collectstatic` or ensure `DEBUG=True` |
| `cardamom1.jpg` not found | Place image at `static/image/cardamom1.jpg` |
