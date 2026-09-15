from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.submissions import router as submissions_router

app = FastAPI(title="English Homework Grader")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(submissions_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
