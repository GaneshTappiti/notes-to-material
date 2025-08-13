# Welcome to your Lovable project

## Project info

**URL**: https://lovable.dev/projects/5fa4be83-e34b-4309-907d-2b424ecb5e69

## How can I edit this code?

There are several ways of editing your application.

**Use Lovable**

Simply visit the [Lovable Project](https://lovable.dev/projects/5fa4be83-e34b-4309-907d-2b424ecb5e69) and start prompting.

Changes made via Lovable will be committed automatically to this repo.

**Use your preferred IDE**

If you want to work locally using your own IDE, you can clone this repo and push changes. Pushed changes will also be reflected in Lovable.

The only requirement is having Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

Follow these steps:

```sh
# Step 1: Clone the repository using the project's Git URL.
git clone <YOUR_GIT_URL>

# Step 2: Navigate to the project directory.
cd <YOUR_PROJECT_NAME>

# Step 3: Install the necessary dependencies.
npm i

# Step 4: Start the development server with auto-reloading and an instant preview.
npm run dev
```

**Edit a file directly in GitHub**

- Navigate to the desired file(s).
- Click the "Edit" button (pencil icon) at the top right of the file view.
- Make your changes and commit the changes.

**Use GitHub Codespaces**

- Navigate to the main page of your repository.
- Click on the "Code" button (green button) near the top right.
- Select the "Codespaces" tab.
- Click on "New codespace" to launch a new Codespace environment.
- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## Auto Q&A from Notes (New Feature)

An experimental wizard flow lets you upload chapter-wise notes and (in production) generate exam-style questions (2M / 5M / 10M) plus sourced answers strictly from the uploaded PDFs. The current UI includes:

- New job type selection: "Auto Q&A from Notes".
- Generation settings (marks, counts, mode, sourcing toggles).
- Preview step with mock generation (front-end only for now) showing FOUND / NOT_FOUND / NEEDS_REVIEW statuses and confidence.

Backend responsibilities (to be implemented separately): OCR, embeddings, retrieval, guarded model prompting, validation, and export using the JSON schema in `src/types/autoqa.ts`.

Database / persistence wiring is intentionally deferred.

## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/5fa4be83-e34b-4309-907d-2b424ecb5e69) and click on Share -> Publish.

## Can I connect a custom domain to my Lovable project?

Yes, you can!

To connect a domain, navigate to Project > Settings > Domains and click Connect Domain.

Read more here: [Setting up a custom domain](https://docs.lovable.dev/tips-tricks/custom-domain#step-by-step-guide)

---

## Minimal Skeleton (Backend + Frontend + Compose)

This repository now includes a minimal working skeleton as requested:

- FastAPI backend (`backend/app/main.py`) mounting only the uploads router (`backend/app/api/uploads.py`).
- POST `/api/uploads` accepts a multipart file and writes it to `STORAGE_PATH` (env) or `./storage`, returning `{ filename, size }`.
- Stub PDF extraction function at `backend/app/services/pdf_extract.py` with a TODO to implement real logic later.
- Simple React upload page (`frontend/src/pages/UploadPage.jsx`) served via Vite that can send a file to the backend.
- `infra/docker-compose.yml` orchestrates `backend`, `frontend`, and `postgres` services. Run from `infra/`:

```sh
docker compose up --build
```

Backend: http://localhost:8000 (health at `/health`)

Frontend: http://localhost:5173

Environment var `VITE_BACKEND_URL` can be used on the frontend to point to a different backend origin.

### Local Development
Backend:
```
cd backend/app
uvicorn app.main:app --reload
```
Frontend:
```
npm install
npm run dev
```
Run backend tests:
```
cd backend/app
pytest -q
```
Healthcheck script:
```
bash scripts/healthcheck.sh
```

### Environment Variables & Secrets

Create `backend/.env` (a template is in `backend/.env.example`):

```bash
GOOGLE_API_KEY=your_gemini_key
JWT_SECRET=change_me
DAILY_CALL_LIMIT=0
```

Never commit real keys. `.gitignore` already excludes `.env` files.

If a key is ever leaked, rotate it in the provider console and update your `.env` / deployment secrets immediately.

### Secret Scanning Pre-Commit Hook

Optional but recommended:

```bash
pip install pre-commit detect-secrets
pre-commit install
```

Regenerate baseline when intentional changes occur:

```bash
detect-secrets scan > .secrets.baseline
```

This will block commits that introduce high-entropy potential secrets.

### Authentication & Roles

JWT auth added:

- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me

Roles: student | faculty | admin. First registered user becomes admin. Faculty/admin can approve questions at `PATCH /api/questions/{id}/approve`.

### CI

GitHub Actions workflows: backend tests & frontend lint/test under `.github/workflows`.

### Metrics & Monitoring

Prometheus endpoint at `/metrics`. See `monitoring/README.md`.

### TODOs / Next Steps

- Real PDF parsing & OCR improvements.
- Postgres migrations.
- Additional unit + integration tests (embedding, generator mocks etc.).
- Add rate limiting / budgeting around Gemini calls.
- Tighten CORS and add refresh tokens.
