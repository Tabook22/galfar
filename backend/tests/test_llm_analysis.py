import json

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_llm_analysis_stores_nested_fields_as_text():
    llm_payload = {
        "summary": "Financial overview.",
        "revenue": {"total_revenue": "$100,000"},
        "expenses": {"total_expenses": "$80,000"},
        "profit_loss": {"net_profit": "$20,000"},
        "cash_flow": {"net_cash_flow": "$20,000"},
        "assets": ["cash", "inventory"],
        "liabilities": None,
        "risks": "Market risk.",
        "strengths": "Strong revenue.",
        "weaknesses": "High expenses.",
        "recommendations": "Reduce costs.",
    }

    upload = client.post(
        "/api/reports",
        files={"file": ("sales.txt", b"Total Revenue: $100,000", "text/plain")},
    )
    report_id = upload.json()["id"]

    with patch(
        "app.services.analysis_service.LLMService.analyze_report",
        new=AsyncMock(return_value=llm_payload),
    ):
        response = client.post(f"/api/reports/{report_id}/analysis", json={"force": True})

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["revenue"] == json.dumps(llm_payload["revenue"], ensure_ascii=False)
    assert body["assets"] == json.dumps(llm_payload["assets"], ensure_ascii=False)
