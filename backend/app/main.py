from fastapi import FastAPI

app = FastAPI(title="English Homework Grader")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
