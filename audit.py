import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"
LOG_FILE = LOG_DIR / "audit.jsonl"


def log_event(question: str, result: dict, status: str = "success", error: str | None = None):
    """Append a minimal audit record. Avoid storing secrets or full document text."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "status": status,
        "answer": result.get("answer", "")[:2000],
        "sources": [
            {"citation": s.get("citation"), "source": s.get("source"), "page": s.get("page")}
            for s in result.get("sources", [])
        ],
    }
    if error:
        record["error"] = error[:500]
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
