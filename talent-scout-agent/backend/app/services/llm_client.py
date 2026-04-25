"""
Centralized LLM client — Groq edition.
Drop-in replacement for the Anthropic version.
All agents call through here unchanged.
"""
import os
import json
import re
from typing import Optional, Type, TypeVar
from groq import Groq
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Groq model names. llama-3.3-70b is the best free model for this task.
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
FAST_MODEL = os.getenv("GROQ_FAST_MODEL", "llama-3.1-8b-instant")


class LLMClient:
    """Singleton-ish wrapper around Groq SDK."""

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY env var is required. "
                "Get one free at https://console.groq.com/"
            )
        self.client = Groq(api_key=api_key)

    def complete(
        self,
        system: str,
        user: str,
        model: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """Plain text completion."""
        model = model or DEFAULT_MODEL
        try:
            resp = self.client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def complete_json(
        self,
        system: str,
        user: str,
        schema: Type[T],
        model: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> T:
        """
        Completion that returns a parsed Pydantic model.
        Uses Groq's JSON mode for guaranteed valid JSON output.
        """
        json_system = (
            f"{system}\n\n"
            "CRITICAL: Respond with ONLY a single valid JSON object matching the requested schema. "
            "No markdown fences, no commentary, no preamble. Just the JSON object."
        )

        model = model or DEFAULT_MODEL
        try:
            resp = self.client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                response_format={"type": "json_object"},  # Groq's JSON mode
                messages=[
                    {"role": "system", "content": json_system},
                    {"role": "user", "content": user},
                ],
            )
            raw = resp.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM JSON call failed: {e}")
            raise

        parsed = self._extract_json(raw)
        return schema(**parsed)

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Defensive JSON extraction — handles fences and surrounding prose."""
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise ValueError(f"Could not parse JSON from LLM response: {text[:300]}")


# Module-level singleton
_client: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client