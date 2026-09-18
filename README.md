# MedVision AI

An AI-powered healthcare education platform: image, voice, and text understanding combined with
Retrieval-Augmented Generation (RAG) over a real, admin-managed medical knowledge base.

> **MedVision AI is not a licensed medical professional.** Every prediction, chat reply, and report it
> produces is general AI-generated educational information — never a diagnosis, and never a substitute
> for seeing a licensed doctor. This disclaimer is shown throughout the app itself, not just here.

---

## What's actually in this build (read this first)

This is a complete, working, end-to-end platform — backend, frontend, database, RAG pipeline, image
classifier, speech-to-text, OCR, PDF reports, admin tooling, Docker deployment, CI, and tests are all
real and have been run successfully against a live MySQL + Redis stack during development. Three things
are worth being explicit about before you deploy this anywhere real:

1. **The disease/symptom/medication knowledge base is a starter set, not a medical reference.**
   `scripts/seed_data.py` populates ~20 diseases and ~35 symptoms with simplified, general-public
   educational content so the platform is usable immediately. Before any real-world use, this content
   needs review and expansion by qualified medical professionals through the Admin → Diseases panel.

2. **The image classifier is trained on a synthetic, procedurally-generated demo dataset**, not real
   clinical photos (those require licensed, IRB-approved datasets like ISIC, which aren't available in
   this environment). The full pipeline — quality gate, feature extraction, classification, explanation —
   genuinely works, but its predictions are not clinically meaningful. See
   `backend/app/services/vision/synthetic_dataset.py` for the full explanation and what's needed to swap
   in real data (the Admin → Image Dataset Builder / Active Learning flow exists specifically for this).

3. **Gemini and Whisper require your own API key / internet access** to run with full natural-language
   and speech capability. Without a `GEMINI_API_KEY`, the chatbot still works correctly — it falls back to
   a deterministic, still-RAG-grounded template response instead of an LLM-polished one. Whisper needs the
   `ffmpeg` binary and downloads its model checkpoint on first use (~140MB for the default `base` model).
   
4. **Yandex Maps API (optional) enables smart emergency routing.** Set `YANDEX_API_KEY` to power the
   emergency locator with turn-by-turn directions to the nearest hospital/pharmacy, including distance,
   estimated travel time, and interactive maps. Without the key, the system falls back to Haversine-based
   distance-only search (still fully functional).

Everything else — auth, RBAC, the knowledge base CRUD, the explainable disease-prediction algorithm, FAISS
vector search, OCR lab-report parsing, PDF generation, health scoring, audit logs, Celery background jobs —
is fully functional, no asterisks.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, TypeScript, TailwindCSS, Redux Toolkit, Axios, Framer Motion, Chart.js |
| Backend | Python, FastAPI, SQLAlchemy 2.0, Alembic, JWT (access + refresh), Redis, Celery |
| Database | MySQL 8 (MariaDB-compatible) |
| AI / ML | scikit-learn, FAISS, OpenCV, Whisper, Gemini API (`google-genai`) |
| Maps & Routing | Yandex Maps API (routes + static maps) |
| Docs/PDF | ReportLab, pytesseract, pypdf, python-docx |

---

## Quick start (Docker — recommended)

```bash
cp .env.example backend/.env
# Edit backend/.env and set GEMINI_API_KEY and YANDEX_API_KEY if you have them (both optional — app works without)

docker compose up --build
```

This starts MySQL, Redis, the FastAPI backend (auto-runs migrations, trains the demo vision model, and
seeds the knowledge base on first boot), a Celery worker, and the frontend (served via nginx on port 80).

- Frontend: http://localhost
- API docs (Swagger UI): http://localhost:8000/docs
- API docs (ReDoc): http://localhost:8000/redoc

**Demo accounts** (created by the seed script):

| Role | Email | Password |
|---|---|---|
| Admin | admin@medvision.ai | Admin@12345 |
| Doctor | doctor@medvision.ai | Doctor@12345 |
| Patient | patient@medvision.ai | Patient@12345 |

---

## Manual setup (without Docker)

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# System dependencies you'll need on the host:
#   ffmpeg        (Whisper audio decoding)
#   tesseract-ocr (lab report OCR)

cp ../.env.example .env
# Edit .env: set DATABASE_URL to your MySQL instance (or sqlite:///./medvision_dev.db for zero-setup dev)
# Optional: set GEMINI_API_KEY and YANDEX_API_KEY for LLM and smart routing features

alembic upgrade head
python scripts/train_vision_model.py   # trains the demo vision classifier (~30 seconds)
python scripts/seed_data.py            # seeds knowledge base + demo accounts

uvicorn app.main:app --reload
```

If you prefer to start the backend from the repository root instead of changing into `backend/`, use:

```bash
uvicorn app.main:app --reload --app-dir backend
```

In a second terminal, start the Celery worker (needed for vision model retraining from the admin panel):

```bash
celery -A app.core.celery_app worker --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173 — the Vite dev server proxies `/api` to `http://localhost:8000`.

### Tests

```bash
cd backend
pytest tests/ -v
```

---

## Project structure

```
medvision-ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # All REST endpoints, one file per resource
│   │   ├── core/                # Config, security (JWT/bcrypt), Celery app, rate limiting
│   │   ├── db/                  # SQLAlchemy base + session
│   │   ├── models/               # ORM models (18 tables — see docs/ER_DIAGRAM.md)
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── rag/              # Embeddings, FAISS vector store, indexer, retriever
│   │   │   ├── llm/               # Gemini client with RAG-grounded prompting + fallback
│   │   │   ├── vision/            # Image quality gate, feature extraction, classifier
│   │   │   ├── speech/            # Whisper transcription
│   │   │   ├── nlp/               # Symptom extraction, lab report OCR parsing
│   │   │   └── ml/                # Explainable disease-prediction algorithm
│   │   └── tasks/                 # Celery background tasks
│   ├── alembic/                   # DB migrations
│   ├── scripts/                   # train_vision_model.py, seed_data.py
│   └── tests/                     # pytest suite
├── frontend/
│   └── src/
│       ├── pages/                 # One file per route, pages/admin/ for the admin sub-tabs
│       ├── components/            # Layout, ProtectedRoute, shared UI
│       ├── store/                 # Redux Toolkit slices (auth, ui)
│       ├── api/                   # Axios client + typed API call wrappers
│       └── i18n/                  # English / Uzbek / Russian translations
├── docs/
│   ├── ER_DIAGRAM.md              # Mermaid entity-relationship diagram
│   └── openapi.json               # Exported OpenAPI spec
├── docker-compose.yml
└── .github/workflows/ci.yml       # Backend tests + frontend build on every push
```

---

## Architecture: how a request actually flows

**Text symptom check:**
`POST /diagnosis/text` → `services/nlp/symptom_extractor.py` matches free text against the knowledge-base
Symptom table → `services/ml/disease_predictor.py` scores candidate diseases using a transparent,
explainable weighted-coverage algorithm over the Disease↔Symptom graph (see that file's docstring for the
full math) → results + matched symptoms + feature importances are persisted and returned.

**AI chat / RAG:**
`POST /chat/send` → `services/rag/retriever.py` embeds the query (TF-IDF+SVD by default, or Gemini
embeddings if configured) and searches the FAISS index → top matches are passed as grounding context to
`services/llm/gemini_client.py`, which is instructed to answer **only** from that context → if no API key
or the call fails, a deterministic template response is built directly from the same retrieved context, so
the feature never silently breaks.

**Knowledge base updates are instantly searchable:** every Disease/Symptom/Medication/Article create,
update, or delete triggers `services/rag/indexer.py::reindex_all`, which rebuilds the FAISS index from the
current DB state — no LLM retraining step, ever.

**Image diagnosis:**
`POST /diagnosis/image` → `services/vision/quality_check.py` rejects blurry/dark/low-res photos using
Laplacian-variance blur detection → `services/vision/features.py` extracts HSV color-histogram + texture
features → `services/vision/classifier.py` runs the per-body-part RandomForest model → result is cross-
referenced against the Disease table for educational context.

---

## Security

JWT access + refresh tokens, bcrypt password hashing, role-based access control (admin/doctor/patient)
enforced via FastAPI dependencies, per-IP rate limiting, file upload validation (type/size), parameterized
queries throughout (SQLAlchemy ORM — no raw SQL string interpolation), and an audit log recording every
sensitive admin/auth action.

## License & disclaimer

Educational/demonstration use. Not a certified medical device. Review all medical content with qualified
professionals before any real-world deployment.
