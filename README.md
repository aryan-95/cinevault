# CineVault

CineVault is an original, full-stack movie streaming web application built with Python and Flask. It includes authentication, a browsable catalog, a video player with resume support, ratings & reviews, a rule-based recommendation engine, and a full admin dashboard — all running on a clean, modular Flask codebase.

> All demo content (movies, cast, posters) is fictional. Poster/backdrop images are placeholder images and sample videos are freely licensed public test clips (Big Buck Bunny / Elephants Dream). No pirated or copyrighted streaming content is used or referenced.

---

## 1. Features

- **Authentication**: register, login, logout, remember-me, change password, delete account, USER/ADMIN roles
- **Homepage**: hero banner, Continue Watching, Recommended For You, Trending, Popular, Recently Added, and per-genre rows
- **Movie details page** with cast, director, genres, ratings, and similar movies
- **Video player** (`/watch/<id>`) with play/pause/seek/volume/fullscreen/speed (native HTML5 controls), HLS.js fallback for `.m3u8` sources, and automatic resume-from-position
- **Search** by title/genre/cast/director/description with filters (genre, year, rating, language) and pagination
- **Genre pages** (`/genre/<name>`)
- **My List**: add/remove/view, duplicate-safe
- **Continue Watching**: tracks progress, resumes playback, shows completion %
- **Ratings & reviews**: 1–5 stars, one review per user per movie, edit/delete
- **Recommendation engine**: rule-based genre-affinity scoring (`app/services/recommendation_service.py`), designed to be swapped for an ML model later without touching routes
- **Admin dashboard** (`/admin`): stats, movie CRUD with file uploads, user management (search/disable/delete/change role), analytics charts (Chart.js)
- **REST API** under `/api/*` for auth, movies, search, my-list, watch history/progress, and reviews
- **Storage abstraction** (`app/services/storage_service.py`): local filesystem today, drop-in S3/CloudFront backend later
- **Optional FFmpeg/HLS** conversion with automatic MP4 fallback if FFmpeg isn't installed

---

## 2. Tech Stack

**Backend:** Python 3.12, Flask, SQLAlchemy, Flask-Login, Flask-Migrate, Flask-WTF (CSRF), Werkzeug password hashing, SQLite (dev) / PostgreSQL (prod)

**Frontend:** HTML5, CSS3 (custom dark theme), vanilla JavaScript, Bootstrap 5, Chart.js, HLS.js

**Infra:** Docker, Docker Compose, Gunicorn, `.env`-based configuration

**Testing:** Pytest (39 tests covering auth, movies, search, my-list, watch progress, reviews, and admin authorization)

---

## 3. Project Structure

```text
cinevault/
├── app/
│   ├── __init__.py            # App factory
│   ├── decorators.py          # @admin_required
│   ├── models/                # user, movie, review, watch_history, my_list
│   ├── routes/                # auth, main, movies, api, admin
│   ├── services/               # storage_service, video_service, recommendation_service
│   ├── templates/              # Jinja templates (+ admin/, errors/, partials/)
│   └── static/                 # css/, js/, icons/
├── config.py                   # Dev/Prod/Testing config classes
├── run.py                      # Local dev entrypoint
├── scripts/seed.py             # Seeds admin/demo users + 20 demo movies
├── tests/                      # Pytest suite
├── media/                      # Local uploads (movies/posters/backdrops/trailers/subtitles)
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 4. Installation (local, SQLite)

```bash
git clone <this-project>
cd cinevault

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env            # edit values as needed
```

### Seed the database

```bash
python scripts/seed.py
```

This creates:
- Admin user: value of `ADMIN_EMAIL` / `ADMIN_PASSWORD` from `.env` (defaults to `admin@example.com` / `change-me` — **change this**)
- Demo user: `demo@example.com` / `demopassword123`
- 20 fictional movies with placeholder posters and sample video sources

### Run locally

```bash
python run.py
```

Visit `http://localhost:5000`.

---

## 5. Docker

```bash
docker compose up --build
```

This starts the Flask app (Gunicorn) + PostgreSQL, creates tables automatically on boot. Then seed it:

```bash
docker compose exec web python scripts/seed.py
```

Set `SECRET_KEY`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD` via a `.env` file or your shell before running `docker compose up` in production.

---

## 6. Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Flask session/CSRF signing key — set a long random value |
| `DATABASE_URL` | SQLite for dev, PostgreSQL URL for production |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Used by `scripts/seed.py` to create the admin account |
| `UPLOAD_FOLDER` | Where uploaded media is stored locally |
| `STORAGE_BACKEND` | `local` (default) or `s3` (see `storage_service.py`) |

Never commit your real `.env` file.

---

## 7. API Reference

```text
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/logout

GET    /api/movies
GET    /api/movies/<id>
POST   /api/movies            (admin)
PUT    /api/movies/<id>       (admin)
DELETE /api/movies/<id>       (admin)

GET    /api/search?q=...
GET    /api/genres/<genre>

GET    /api/my-list
POST   /api/my-list/<movie_id>
DELETE /api/my-list/<movie_id>

GET    /api/watch-history
POST   /api/watch-progress

POST   /api/reviews
PUT    /api/reviews/<id>
DELETE /api/reviews/<id>
```

All endpoints return JSON with standard HTTP status codes (200/201/400/401/403/404/409).

---

## 8. Testing

```bash
pytest
```

39 tests cover registration/login/logout, movie listing & detail, search, genre pages, My List, watch progress + Continue Watching, review CRUD + duplicate prevention, and admin-only authorization on both HTML and JSON routes.

Verification also performed on this build:

```bash
python -m compileall .   # no syntax errors
pytest                   # 39 passed
```

---

## 9. Adding Movies

Two ways:

1. **Admin UI**: log in as an admin → `/admin/movies` → "Add Movie". Upload a poster/backdrop/video file, or paste direct URLs instead of uploading.
2. **API**: `POST /api/movies` (admin session required) with JSON fields matching the `Movie` model.

## 10. How Video Streaming Works

- Videos are served from `media/movies/` (or wherever `UPLOAD_FOLDER` points) via the `/media/<path>` route.
- If a stored `video_url` ends in `.m3u8`, the player uses HLS.js (or native HLS on Safari) for adaptive streaming.
- Otherwise, the browser's native `<video>` tag plays the MP4 directly — no FFmpeg required for local development.
- `app/services/video_service.py` provides `convert_to_hls()`, which uses FFmpeg to transcode an uploaded MP4 into an HLS playlist + `.ts` segments if FFmpeg is available on the host; if not, the app transparently falls back to serving the original MP4.
- Playback position is saved via `POST /watch/<id>/progress` every 10 seconds and on pause/unload, and used to resume playback and populate "Continue Watching".

## 11. Security Notes

- Passwords hashed with Werkzeug (`generate_password_hash` / `check_password_hash`)
- CSRF protection (Flask-WTF) on all state-changing form submissions; JSON API endpoints that don't use browser cookies are explicitly exempted
- File upload validation by extension allow-list, `secure_filename()`, unique generated filenames, and `MAX_CONTENT_LENGTH`
- Admin-only routes protected by an `@admin_required` decorator plus a blueprint-level `before_request` guard
- No secrets are hard-coded — all pulled from environment variables via `config.py`

## 12. Production Deployment Notes

- Set `FLASK_ENV=production`, a strong `SECRET_KEY`, and `SESSION_COOKIE_SECURE=true` behind HTTPS
- Point `DATABASE_URL` at PostgreSQL (already the default in `ProductionConfig` / `docker-compose.yml`)
- Put a reverse proxy (nginx) in front of Gunicorn for TLS termination and static file caching
- Swap `STORAGE_BACKEND=s3` and implement `S3StorageService` in `storage_service.py` for object storage + CloudFront
- Run `flask db upgrade` (Flask-Migrate) instead of `db.create_all()` once you've generated migrations for schema changes

## 13. Future Improvements

- Replace the rule-based recommender with a learned model (collaborative filtering / embeddings) — the service interface is already isolated for this
- Real HLS adaptive bitrate ladders (multiple renditions) instead of single-rendition HLS
- Email verification and password-reset flows
- Server-side pagination for the admin movie/user tables
- WebSocket-based "currently watching" presence indicators
- Multi-language subtitle tracks and localized UI

---

## Default Local Credentials (after seeding)

| Role | Email | Password |
|---|---|---|
| Admin | value of `ADMIN_EMAIL` in `.env` | value of `ADMIN_PASSWORD` in `.env` |
| Demo user | `demo@example.com` | `demopassword123` |

**Change these before any real deployment.**
