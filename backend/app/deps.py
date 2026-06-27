from fastapi import Header

from app.i18n.locale import normalize_language


def resolve_language(
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
    body_language: str | None = None,
) -> str:
    if body_language:
        return normalize_language(body_language)
    if accept_language:
        return normalize_language(accept_language)
    return "en"
