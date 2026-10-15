from fastapi.testclient import TestClient
import api

client = TestClient(api.app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_empty_question_rejected():
    response = client.post("/ask", json={"question": "   "})
    assert response.status_code in (400, 422)
