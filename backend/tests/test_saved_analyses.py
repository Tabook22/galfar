import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_save_and_list_report_analysis():
    upload = client.post(
        "/api/reports",
        files={"file": ("sales.txt", b"Total Revenue: $100,000\nNet Profit: $20,000", "text/plain")},
    )
    assert upload.status_code == 201
    report_id = upload.json()["id"]

    analysis = client.post(f"/api/reports/{report_id}/analysis", json={"force": True})
    assert analysis.status_code == 201

    saved = client.post(
        f"/api/saved-analyses/reports/{report_id}",
        json={"title": "Q1 Sales Review"},
    )
    assert saved.status_code == 201
    body = saved.json()
    assert body["title"] == "Q1 Sales Review"
    assert body["source_type"] == "report"
    assert body["filename"].endswith(".json")
    assert body["filename"].startswith("20")

    listing = client.get("/api/saved-analyses")
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    detail = client.get(f"/api/saved-analyses/{body['id']}")
    assert detail.status_code == 200
    assert detail.json()["content"]["title"] == "Q1 Sales Review"
    assert detail.json()["content"]["analysis"]["summary"]

    deleted = client.delete(f"/api/saved-analyses/{body['id']}")
    assert deleted.status_code == 204
    assert client.get("/api/saved-analyses").json() == []


def test_update_saved_report_analysis():
    upload = client.post(
        "/api/reports",
        files={"file": ("sales.txt", b"Total Revenue: $100,000\nNet Profit: $20,000", "text/plain")},
    )
    report_id = upload.json()["id"]
    client.post(f"/api/reports/{report_id}/analysis", json={"force": True})

    saved = client.post(
        f"/api/saved-analyses/reports/{report_id}",
        json={"title": "Payments Review"},
    )
    saved_id = saved.json()["id"]

    updated = client.patch(
        f"/api/saved-analyses/{saved_id}",
        json={
            "title": "Updated Payments",
            "summary": "Revised executive summary.",
            "revenue": "150,000",
            "custom_sections": [
                {"title": "Auditor notes", "content": "Verified by finance team."}
            ],
        },
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["title"] == "Updated Payments"
    assert body["content"]["analysis"]["summary"] == "Revised executive summary."
    assert body["content"]["analysis"]["revenue"] == "150,000"
    assert body["content"]["custom_sections"][0]["title"] == "Auditor notes"
    assert body["content"]["last_edited_at"]


def test_update_saved_document_html():
    upload = client.post(
        "/api/reports",
        files={"file": ("sales.txt", b"Total Revenue: $100,000\nNet Profit: $20,000", "text/plain")},
    )
    report_id = upload.json()["id"]
    client.post(f"/api/reports/{report_id}/analysis", json={"force": True})

    saved = client.post(
        f"/api/saved-analyses/reports/{report_id}",
        json={"title": "Unified Doc Review"},
    )
    saved_id = saved.json()["id"]

    html = "<h2>Summary</h2><p>One unified report body.</p><h2>Revenue</h2><p>100,000</p>"
    updated = client.patch(
        f"/api/saved-analyses/{saved_id}",
        json={"title": "Unified Doc Review", "document_html": html},
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["content"]["document_html"] == html
    assert body["content"]["last_edited_at"]


def test_reanalyze_saved_report_analysis():
    from unittest.mock import AsyncMock, patch

    upload = client.post(
        "/api/reports",
        files={"file": ("sales.txt", b"Total Revenue: $100,000\nNet Profit: $20,000", "text/plain")},
    )
    report_id = upload.json()["id"]
    client.post(f"/api/reports/{report_id}/analysis", json={"force": True})

    saved = client.post(
        f"/api/saved-analyses/reports/{report_id}",
        json={"title": "Cash Flow Review"},
    )
    saved_id = saved.json()["id"]

    llm_payload = {
        "summary": "Focused on cash flow.",
        "revenue": "$100,000",
        "expenses": None,
        "profit_loss": "$20,000",
        "cash_flow": "Positive operating cash flow.",
        "assets": None,
        "liabilities": None,
        "risks": "Liquidity risk is low.",
        "strengths": "Strong collections.",
        "weaknesses": None,
        "recommendations": "Monitor payables.",
    }

    with patch(
        "app.services.analysis_service.LLMService.analyze_report",
        new=AsyncMock(return_value=llm_payload),
    ) as mock_analyze:
        updated = client.post(
            f"/api/saved-analyses/{saved_id}/reanalyze",
            json={"criteria": "Focus on cash flow and liquidity risks."},
        )

    assert updated.status_code == 200
    body = updated.json()
    assert body["content"]["analysis"]["summary"] == "Focused on cash flow."
    assert body["content"]["last_reanalyze_criteria"] == "Focus on cash flow and liquidity risks."
    assert "document_html" not in body["content"]
    mock_analyze.assert_called_once()
    assert mock_analyze.call_args.kwargs["criteria"] == "Focus on cash flow and liquidity risks."


def test_bulk_delete_saved_analyses():
    ids = []
    for i in range(3):
        upload = client.post(
            "/api/reports",
            files={"file": (f"s{i}.txt", b"Revenue: 100", "text/plain")},
        )
        report_id = upload.json()["id"]
        client.post(f"/api/reports/{report_id}/analysis", json={"force": True})
        saved = client.post(
            f"/api/saved-analyses/reports/{report_id}",
            json={"title": f"Review {i}"},
        )
        assert saved.status_code == 201
        ids.append(saved.json()["id"])

    deleted = client.post("/api/saved-analyses/bulk-delete", json={"saved_ids": ids[:2]})
    assert deleted.status_code == 200
    assert deleted.json()["deleted_count"] == 2

    listing = client.get("/api/saved-analyses")
    remaining = {item["id"] for item in listing.json()}
    assert ids[0] not in remaining
    assert ids[1] not in remaining
    assert ids[2] in remaining
