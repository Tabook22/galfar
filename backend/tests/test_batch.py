import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_batch_upload_and_analysis():
    files = [
        ("files", ("r1.txt", b"Total Revenue: $100,000\nNet Profit: $20,000", "text/plain")),
        ("files", ("r2.txt", b"Total Revenue: $50,000\nNet Profit: $10,000", "text/plain")),
    ]
    upload = client.post("/api/batches", files=files, data={"name": "Q1 Batch"})
    assert upload.status_code == 201
    batch_id = upload.json()["id"]
    assert upload.json()["report_count"] == 2

    analysis = client.post(
        f"/api/batches/{batch_id}/analysis",
        json={"force": True, "language": "en"},
        headers={"Accept-Language": "en"},
    )
    assert analysis.status_code == 201
    body = analysis.json()
    assert body["status"] == "completed"
    assert body["summary"]
    assert body["report_count"] == 2

    saved = client.get(f"/api/batches/{batch_id}/report-analyses")
    assert saved.status_code == 200
    items = saved.json()["items"]
    assert len(items) == 2
    assert all(item["analysis"] and item["analysis"]["status"] == "completed" for item in items)

    history = client.get(f"/api/batches/{batch_id}/analysis/history")
    assert history.status_code == 200
    assert len(history.json()) >= 1

    chat = client.post(
        f"/api/batches/{batch_id}/chat",
        json={"message": "Summarize revenue across all reports", "language": "en"},
    )
    assert chat.status_code == 201
    assert chat.json()["assistant_message"]["content"]
    assert "revenue" in chat.json()["assistant_message"]["content"].lower() or "100" in chat.json()["assistant_message"]["content"]
