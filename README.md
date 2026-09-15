# English Homework Grader

MVP project for English teachers to upload scanned student homework and automatically grade student answers.

This repository currently contains the initial technical structure only. OCR, grading, authentication, and database features are not implemented yet.

## Project structure

- `frontend/` — Next.js (TypeScript) web application
- `backend/` — FastAPI REST API
- `docs/` — placeholder product and architecture notes

## Run the frontend

From the `frontend` directory:

```bash
npm install
npm run dev
```

Then open [http://localhost:3000](http://localhost:3000).

## Run the backend

From the `backend` directory:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --app-dir .
```

Then check [http://localhost:8000/health](http://localhost:8000/health).
