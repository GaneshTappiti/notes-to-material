# Scollab Generator Backend (Initial Scaffold)

This is an initial scaffold created by AI assistant. Replace in-memory stores with Postgres, implement workers, and secure API keys.

## Endpoints
- POST /api/uploads
- POST /api/jobs
- GET /api/jobs/{id}/status
- GET /api/jobs/{id}/results
- PATCH /api/questions/{id}
- POST /api/exports

## Next Steps
- Integrate real DB models (SQLAlchemy or Piccolo, etc.)
- Add background task queue
- Implement embedding + retrieval with Chroma
- Implement Gemini generation
- Add PDF export via puppeteer / react-pdf
