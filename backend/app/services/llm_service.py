"""Placeholder LLM provider layer — connect OpenAI or another provider when ready."""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import Settings
from app.i18n.locale import language_instruction, normalize_language


class LLMService:
    """Abstraction over LLM providers. Uses OpenAI when enabled, otherwise returns None."""

    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def is_enabled(self) -> bool:
        return self.settings.llm_ready

    async def analyze_report(
        self,
        report_text: str,
        filename: str,
        language: str = "en",
        criteria: str | None = None,
    ) -> dict[str, Any] | None:
        if not self.is_enabled:
            return None

        lang = normalize_language(language)
        focus_block = ""
        if criteria and criteria.strip():
            focus_block = (
                "IMPORTANT: The user wants this analysis to focus on the following criteria and questions. "
                "Prioritize insights related to these points while still filling all JSON sections:\n"
                f"{criteria.strip()}\n\n"
            )
        prompt = (
            f"{language_instruction(lang)} "
            f"{focus_block}"
            "Analyze the following financial report and return JSON with keys: "
            "summary, revenue, expenses, profit_loss, cash_flow, assets, liabilities, "
            "risks, strengths, weaknesses, recommendations. "
            "All JSON string values must be in the requested language. "
            f"Report filename: {filename}\n\n{report_text[:12000]}"
        )
        return await self._chat_completion(prompt, json_mode=True)

    async def analyze_batch(
        self,
        combined_text: str,
        batch_name: str,
        individual_results: list[dict],
        language: str = "en",
        criteria: str | None = None,
    ) -> dict[str, Any] | None:
        if not self.is_enabled:
            return None

        lang = normalize_language(language)
        breakdown = json.dumps(individual_results[:20], ensure_ascii=False)[:8000]
        focus_block = ""
        if criteria and criteria.strip():
            focus_block = (
                "IMPORTANT: The user wants this combined batch analysis to focus on the following "
                "criteria and questions. Prioritize cross-report insights related to these points:\n"
                f"{criteria.strip()}\n\n"
            )
        prompt = (
            f"{language_instruction(lang)} "
            f"{focus_block}"
            "You are analyzing MULTIPLE financial reports together as one portfolio. "
            "Synthesize the big picture, trends, totals, and cross-report insights. "
            "Return JSON with keys: summary, revenue, expenses, profit_loss, cash_flow, assets, "
            "liabilities, risks, strengths, weaknesses, recommendations. "
            f"Batch name: {batch_name}\n"
            f"Individual report summaries: {breakdown}\n\n"
            f"Combined report text:\n{combined_text[:12000]}"
        )
        return await self._chat_completion(prompt, json_mode=True)

    async def chat_with_batch(
        self,
        combined_text: str,
        batch_name: str,
        history: list[dict[str, str]],
        user_message: str,
        language: str = "en",
        analysis_context: str | None = None,
    ) -> str | None:
        if not self.is_enabled:
            return None

        lang = normalize_language(language)
        analysis_block = f"\n\nSaved analyses:\n{analysis_context[:8000]}" if analysis_context else ""
        messages = [
            {
                "role": "system",
                "content": (
                    f"{language_instruction(lang)} "
                    f"You are a financial analyst reviewing multiple reports in batch '{batch_name}'. "
                    f"Answer using all reports and saved analyses for the big picture.\n\n"
                    f"Combined excerpts:\n{combined_text[:10000]}"
                    f"{analysis_block}"
                ),
            }
        ]
        for msg in history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})
        return await self._raw_chat(messages)

    async def chat_with_report(
        self,
        report_text: str,
        filename: str,
        history: list[dict[str, str]],
        user_message: str,
        language: str = "en",
        analysis_context: str | None = None,
    ) -> str | None:
        if not self.is_enabled:
            return None

        lang = normalize_language(language)
        analysis_block = f"\n\nSaved analysis:\n{analysis_context[:8000]}" if analysis_context else ""
        messages = [
            {
                "role": "system",
                "content": (
                    f"{language_instruction(lang)} "
                    f"You are a financial analyst assistant. Answer questions about the report "
                    f"'{filename}' using the report content and saved analysis when relevant.\n\n"
                    f"Report excerpt:\n{report_text[:8000]}"
                    f"{analysis_block}"
                ),
            }
        ]
        for msg in history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        return await self._raw_chat(messages)

    async def _chat_completion(self, prompt: str, json_mode: bool = False) -> dict[str, Any] | None:
        messages = [{"role": "user", "content": prompt}]
        raw = await self._raw_chat(messages, json_mode=json_mode)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"summary": raw}

    async def _raw_chat(self, messages: list[dict[str, str]], json_mode: bool = False) -> str | None:
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "model": self.settings.openai_model,
            "messages": messages,
            "temperature": 0.3,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=body,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
