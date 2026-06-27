import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_and_list_report():
    content = b"Total Revenue: $1,000,000\nTotal Expenses: $600,000\nNet Profit: $400,000"
    files = {"file": ("report.txt", content, "text/plain")}
    upload = client.post("/api/reports", files=files)
    assert upload.status_code == 201
    report_id = upload.json()["id"]

    listing = client.get("/api/reports")
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["id"] == report_id


def test_run_analysis():
    content = b"Total Revenue: $500,000\nTotal Expenses: $300,000\nNet Profit: $200,000"
    files = {"file": ("finance.txt", content, "text/plain")}
    upload = client.post("/api/reports", files=files)
    report_id = upload.json()["id"]

    analysis = client.post(f"/api/reports/{report_id}/analysis", json={"force": True})
    assert analysis.status_code == 201
    body = analysis.json()
    assert body["status"] == "completed"
    assert body["summary"]


def test_chat_with_report():
    content = b"Total Revenue: $100,000"
    files = {"file": ("small.txt", content, "text/plain")}
    upload = client.post("/api/reports", files=files)
    report_id = upload.json()["id"]

    chat = client.post(f"/api/reports/{report_id}/chat", json={"message": "What is the revenue?"})
    assert chat.status_code == 201
    reply = chat.json()["assistant_message"]["content"]
    assert reply
    assert "100" in reply or "revenue" in reply.lower()
    assert "LLM_ENABLED" not in reply


def test_chat_report_details():
    content = b"Store: Acme Market\nDate: 03/15/2026\nSubtotal: $45.00\nTax: $2.25\nTotal: $47.25"
    files = {"file": ("RECEIPT.txt", content, "text/plain")}
    upload = client.post("/api/reports", files=files)
    report_id = upload.json()["id"]

    chat = client.post(
        f"/api/reports/{report_id}/chat",
        json={"message": "can you give me more details about this report", "language": "en"},
        headers={"Accept-Language": "en"},
    )
    assert chat.status_code == 201
    reply = chat.json()["assistant_message"]["content"]
    assert "Acme Market" in reply or "47.25" in reply or "RECEIPT" in reply
    assert "LLM_ENABLED" not in reply


def test_chat_arabic_language():
    content = b"Total Revenue: $100,000\nNet Profit: $50,000"
    files = {"file": ("report.txt", content, "text/plain")}
    upload = client.post("/api/reports", files=files)
    report_id = upload.json()["id"]

    chat = client.post(
        f"/api/reports/{report_id}/chat",
        json={"message": "أعطني ملخصًا", "language": "ar"},
        headers={"Accept-Language": "ar"},
    )
    assert chat.status_code == 201
    reply = chat.json()["assistant_message"]["content"]
    assert reply
    assert any(word in reply for word in ["تفاصيل", "ملخص", "report.txt", "100"])


def test_get_report_after_upload():
    content = b"Total Revenue: $1,000,000\nNet Profit: $400,000"
    files = {"file": ("report.txt", content, "text/plain")}
    upload = client.post("/api/reports", files=files)
    assert upload.status_code == 201
    report_id = upload.json()["id"]

    detail = client.get(f"/api/reports/{report_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["id"] == report_id
    assert body["original_filename"] == "report.txt"


def test_download_report():
    content = b"Total Revenue: $1,000,000\nNet Profit: $400,000"
    files = {"file": ("report.txt", content, "text/plain")}
    upload = client.post("/api/reports", files=files)
    assert upload.status_code == 201
    report_id = upload.json()["id"]

    response = client.get(f"/api/reports/{report_id}/download")
    assert response.status_code == 200
    assert response.content == content
    assert "report.txt" in response.headers.get("content-disposition", "")


def test_download_missing_report():
    response = client.get("/api/reports/9999/download")
    assert response.status_code == 404


def test_delete_missing_report():
    response = client.delete("/api/reports/9999")
    assert response.status_code == 404


def test_bulk_delete_reports():
    ids = []
    for i in range(3):
        upload = client.post(
            "/api/reports",
            files={"file": (f"r{i}.txt", b"Revenue: 100", "text/plain")},
        )
        assert upload.status_code == 201
        ids.append(upload.json()["id"])

    deleted = client.post("/api/reports/bulk-delete", json={"report_ids": ids[:2]})
    assert deleted.status_code == 200
    assert deleted.json()["deleted_count"] == 2

    listing = client.get("/api/reports")
    assert listing.status_code == 200
    remaining = {item["id"] for item in listing.json()}
    assert ids[0] not in remaining
    assert ids[1] not in remaining
    assert ids[2] in remaining
