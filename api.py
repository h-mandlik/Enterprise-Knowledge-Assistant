from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from audit import log_event
from rag_graph import ask_question

app = FastAPI(
    title="Enterprise Knowledge Assistant API",
    description="Grounded employee Q&A over indexed enterprise documents.",
    version="1.0.0",
)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class Source(BaseModel):
    citation: str
    source: str
    page: int | None = None
    chunk_start: int | None = None
    excerpt: str


class AnswerResponse(BaseModel):
    answer: str
    sources: list[Source]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AnswerResponse)
def ask(request: QuestionRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    try:
        result = ask_question(question)
        log_event(question, result)
        return {
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
        }
    # except Exception as exc:
    #     log_event(question, {}, status="error", error=str(exc))
    #     raise HTTPException(status_code=500, detail="Question processing failed. Check server logs.") from exc
    except Exception as exc:
        error_text = str(exc)
    log_event(question, {}, status="error", error=error_text)

    if "503" in error_text or "UNAVAILABLE" in error_text:
        raise HTTPException(
            status_code=503,
            detail=(
                "The AI service is temporarily busy. "
                "Please wait a moment and try again."
            ),
        ) from exc

    raise HTTPException(
        status_code=500,
        detail="Question processing failed. Please check the server logs.",
    ) from exc