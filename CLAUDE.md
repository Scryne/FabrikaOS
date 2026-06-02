# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

FabrikaOS (FDYS — Fabrika Dijital Yönetim Sistemi) is a Flask-based hybrid MES/ERP platform for the metal manufacturing industry. It is a monolithic server-rendered app (Jinja2 + Bootstrap 5) with real-time features (Socket.IO), a JWT REST API, ML-based prediction services, and async background tasks.

**The codebase is written in Turkish** — module names, model classes, route functions, DB columns, comments, and docstrings are all Turkish (e.g. `Kullanici`=User, `Makine`=Machine, `Calisan`=Employee, `IsEmri`=WorkOrder, `Stok`=Stock, `Kalite`=Quality). Match this convention when adding code; do not anglicize existing names.

## Commands

```powershell
# Setup (first time)
python -m venv venv
venv\Scripts\activate              # Windows; on Linux: source venv/bin/activate
pip install -r requirements.txt

# Database (Flask-Migrate)
flask db upgrade                   # apply migrations
flask db migrate -m "message"      # generate a new migration after model changes
python seed_data.py                # DROPS ALL DATA, recreates tables, loads full demo dataset

# Run the app (dev server, Socket.IO + eventlet, host 0.0.0.0:5000)
python run.py
# Env overrides: FDYS_CONFIG=production|development|testing, FDYS_HOST, FDYS_PORT

# Async worker (optional; requires Redis on localhost:6379)
celery -A celery_worker.celery worker --loglevel=info --pool=solo   # --pool=solo on Windows

# Tests (pytest, in-memory SQLite via 'testing' config)
pytest                             # all tests
pytest tests/test_api.py           # single file
pytest tests/test_api.py::test_name -v   # single test
pytest tests/smoke_test.py         # quick smoke check
```

Demo logins after seeding: `admin/admin123` (yonetici), `selin.aktas/demo123` (isg_uzmani), `mehmet.kaya/demo123` (teknisyen), `merve@ford.com.tr/musteri123` (external customer portal).

## Architecture

**Application factory** (`app/__init__.py`): `create_app(config_name)` wires everything. Config classes live in `config.py` (`DevelopmentConfig`/`ProductionConfig`/`TestingConfig`). Production raises if `FDYS_SECRET_KEY` is left at its default. Extensions (db, migrate, jwt, login_manager, bcrypt, csrf, cache, limiter, socketio) are singletons in `app/extensions.py`, initialized against the app inside the factory.

**Three parallel layers per feature** — when adding/changing a module, expect to touch all three:
- `app/routes/<modul>.py` — Blueprint with the page routes (server-rendered Jinja). Each blueprint is registered in `app/__init__.py::_register_blueprints` (most mount at `/<modul>`, dashboard at `/dashboard`).
- `app/models/<modul>.py` — SQLAlchemy models.
- `app/templates/<modul>/` — Jinja templates.
- Non-trivial business logic lives in `app/services/<modul>_servisi.py` (services), not in routes. Routes stay thin.

**Auth & RBAC** (`app/utils/decorators.py`): roles are `yonetici` (admin, auto-access to everything), `operator`, `teknisyen`, plus specialist roles (`ik_uzmani`, `isg_uzmani`, etc.). Protect routes by stacking decorators in this order:
```python
@bp.route('/ekle', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('makine', 'yazma')   # granular: 'okuma'/'yazma'/'silme', or omit for any-access
@log_action('Makine Ekleme')               # writes audit trail
def ekle(): ...
```
`Kullanici.modul_erisim` is a per-user JSON permission map; `modul_erisim_var_mi(modul, izin_turu)` is the underlying check. `@role_required('yonetici', ...)` is the coarser role-based alternative.

**REST API** (`app/routes/api_v1.py`, mounted at `/api/v1`): JWT auth (Flask-JWT-Extended, access+refresh tokens), separate from the session-based web auth. CSRF is exempted for API routes. See `API_DOKUMANTASYONU.md`.

**Real-time**: Socket.IO (`async_mode='eventlet'`) pushes live machine status / OEE / kiosk updates and emergency marquee notifications. `app/services/mock_engine.py` (`MockDataEngine`) is started from `run.py` to simulate live factory data for demos.

**Prediction / AI** (`app/services/ai/`): numpy + scikit-learn services — `kestirimci_bakim` (predictive maintenance), `oee_tahmin` (OEE trend forecast), `stok_tahmin` (stock forecast), `anomali_tespit` (anomaly detection). `app/services/oee_hesaplama.py` computes OEE (Availability × Performance × Quality).

**Async tasks** (`app/tasks/`, `celery_worker.py`): Celery over Redis for email/SMS/notifications. `make_celery` wraps tasks in the Flask app context. Redis/Celery are optional — the app runs without them, only async tasks are disabled.

**Seeding** (`seed_data.py` + `seeds/`): `seed_data.py` drops the DB and runs each `seeds/seed_<modul>.py` in a strict dependency order (users → machines → production → logistics → ... → analytics). When adding a seed for a new module, insert it at the correct dependency position in `run_seeds()`.

## Conventions & Gotchas

- **SQLite WAL is enabled** via a SQLAlchemy connect-event PRAGMA hook (`_configure_sqlite`); production prefers PostgreSQL (`DATABASE_URL`), where `init_app` switches to connection pooling instead.
- **Migrations use `render_as_batch=True`** (batch mode) — required for SQLite ALTER TABLE. Always go through `flask db migrate`/`upgrade` rather than editing the schema by hand.
- **Security headers + CSP** are set globally in `_register_security_headers`; if you add a new external CDN/script source, update the CSP string there or it will be blocked.
- `instance/fdys.db` is the dev database; `instance/` and `app/static/uploads/` are auto-created on startup.
- Root-level `fix_*.py`, `scratch_*.py`, `check_oee.py`, `update_demo_erisim.py` are one-off maintenance/scratch scripts, not part of the app.
- Secrets/config come from environment (`.env` via python-dotenv): `FDYS_SECRET_KEY`, `JWT_SECRET_KEY`, `DATABASE_URL`, `CELERY_BROKER_URL`, etc.
