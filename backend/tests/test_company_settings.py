from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_default_company_settings():
    response = client.get("/api/settings/company")
    assert response.status_code == 200
    body = response.json()
    assert body["company_name"]["en"] == "Galfar"
    assert body["company_name"]["ar"] == "جلفار"
    assert body["page_title"]["en"]


def test_update_bilingual_company_settings():
    updated = client.put(
        "/api/settings/company",
        json={
            "company_name": {"en": "Galfar Gases", "ar": "غالفار للغازات"},
            "page_title": {
                "en": "Galfar Gases — Reports",
                "ar": "غالفار للغازات — التقارير",
            },
            "tagline": {"en": "Industrial gas solutions", "ar": "حلول الغازات الصناعية"},
            "address": {"en": "Muscat, Oman", "ar": "مسقط، عُمان"},
            "industry": {"en": "Industrial gases", "ar": "الغازات الصناعية"},
            "history": {"en": "Founded in 1990.", "ar": "تأسست عام 1990."},
            "introduction_html": {
                "en": "<p>Leading gas supplier.</p>",
                "ar": "<p>مورد رائد للغازات.</p>",
            },
            "phone": "+968 1234 5678",
            "email": "info@galfar.com",
            "website": "https://galfar.com",
        },
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["company_name"]["en"] == "Galfar Gases"
    assert body["company_name"]["ar"] == "غالفار للغازات"
    assert body["address"]["ar"] == "مسقط، عُمان"
    assert body["updated_at"]

    fetched = client.get("/api/settings/company")
    assert fetched.json()["company_name"]["ar"] == "غالفار للغازات"


def test_upload_company_logo():
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    response = client.post(
        "/api/settings/company/logo",
        files={"file": ("logo.png", png_bytes, "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["logo_url"] == "/api/settings/company/logo"

    logo = client.get("/api/settings/company/logo")
    assert logo.status_code == 200
    assert logo.content == png_bytes
