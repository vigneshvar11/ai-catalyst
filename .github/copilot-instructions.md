# AI CatalyESt — Copilot Instructions

## Architecture Overview

This is a **full-stack single-page application** (SPA) with dual backend implementations:

- **Primary backend**: `app.py` — Python Flask + Flask-SocketIO (use `python app.py` to run)
- **Alternate backend**: `server.js` — Node.js Express + Socket.IO (use `node server.js`)
- **Frontend**: Vanilla HTML/CSS/JS SPA in `public/` — no build step, no framework
- **Database**: Single JSON file at `data/db.json` — read/write with `read_db()`/`write_db()` (Python) or `readDB()`/`writeDB()` (Node)

Both backends expose **identical REST APIs and WebSocket events** on port 3000. Only run one at a time.

```
Browser (public/index.html + app.js)  ◄──HTTP REST──►  Flask or Express  ◄──►  data/db.json
                                      ◄──WebSocket───►  SocketIO
```

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Flask backend — all API routes + SocketIO quiz/survey handlers |
| `server.js` | Express backend — mirror of app.py in Node.js |
| `public/index.html` | Single HTML page with all tab sections (dashboard, leaderboard, calendar, team, quiz, admin panels) |
| `public/js/app.js` | All frontend logic — SPA navigation, rendering, quiz client, survey client, admin CRUD |
| `public/css/styles.css` | Siemens-themed styling with CSS custom properties |
| `data/db.json` | Flat-file JSON database — **the single source of truth** for all data |
| `generate_report.py` | Standalone script to produce a Word (.docx) report — not part of the web app |

## Data Model (db.json)

The database has these top-level collections: `config`, `members`, `events`, `points`, `quizzes`, `surveys`, `teams`.

- **Member IDs** are slug-derived from names: `"vigneshvar-sa"`, `"balaji-m"` — generated via `name.lower().replace(' ', '-')`
- **Entity IDs** use prefixed short UUIDs: `"event-a1b2c3d4"`, `"quiz-..."`, `"pts-..."`, `"survey-..."`
- **Points** reference `memberId` and `month` (1–12 integer); leaderboard is computed on read, not stored
- **Events** represent the 12-month plan; each has `month`, `phase` (SPARK/BUILD/APPLY/DELIVER), `seminarPresenter` (member ID), and `status`

## API Conventions

All routes are under `/api/`. Standard CRUD pattern:

```
GET    /api/{resource}          → list all
POST   /api/{resource}          → create (JSON body)
PUT    /api/{resource}/:id      → update (JSON body, spread-merge)
DELETE /api/{resource}/:id      → delete
```

Resources: `members`, `events`, `points`, `quizzes`, `surveys`, `teams`. Special endpoints:
- `GET /api/leaderboard` — computed aggregation of points by member
- `POST /api/members/:id/avatar` — multipart file upload to `uploads/avatars/`
- `POST /api/surveys/:id/vote` — anonymous rating submission
- `POST /api/auth/login` — hardcoded admin check against `db.config.admin`

## WebSocket Events (Quiz & Survey)

Real-time features use Socket.IO with a `quiz:` and `survey:` event namespace pattern:
- Quiz lifecycle: `quiz:create` → `quiz:join` → `quiz:start` → `quiz:answer` → `quiz:finished` → `quiz:end`
- Anti-cheat: `quiz:tabSwitch` triggers a penalty counter; final score = `score - tabSwitches`
- Questions are shuffled per-participant server-side
- Survey: `survey:started` / `survey:voteReceived` / `survey:ended` broadcast to all clients

## Frontend Patterns

- **SPA routing**: Tab switching via `data-tab` attributes; `switchTab(tab)` shows `#tab-{name}` sections
- **Global state**: `const state = { members, events, points, leaderboard, quizzes, surveys, ... }` loaded at startup via `loadAllData()`
- **Admin auth**: Token stored in `localStorage`; admin-only nav buttons have class `.admin-only` toggled via `style.display`
- **Rendering**: Each tab has a dedicated `render*()` function (e.g., `renderLeaderboard()`, `renderCalendar()`); all generate HTML strings via template literals
- **API helper**: `api(url, options)` wraps `fetch()` with auth token injection

## Development Workflow

```bash
# Python (primary)
pip install -r requirements.txt   # flask, flask-socketio
python app.py                     # starts on http://localhost:3000

# Node.js (alternate)
npm install                       # express, socket.io, multer, uuid
node server.js                    # starts on http://localhost:3000
```

- No build step, no transpilation — edit files and refresh the browser
- Admin login: username `admin`, password `admin`
- Avatar uploads saved to `uploads/avatars/{member-id}.{ext}`

## Important Conventions

- **Keep backends in sync**: Any API or WebSocket change must be mirrored in both `app.py` and `server.js`
- **db.json is the database**: Never introduce a separate database without migrating. All writes use the `write_db()`/`writeDB()` helpers that pretty-print with 2-space indent
- **No frontend framework**: Use vanilla JS with template-literal HTML. Follow the existing `render*()` function pattern in `app.js`
- **ID generation**: Members get slug IDs from names; all other entities use `{prefix}-{8-char-uuid}`
- **Update pattern**: Both backends use spread-merge (`{...existing, ...newData}`) for PUT operations, preserving the `id` field
