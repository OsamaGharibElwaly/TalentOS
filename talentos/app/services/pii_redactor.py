from __future__ import annotations

import re
from dataclasses import dataclass

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
LINK_RE = re.compile(r"https?://[^\s<>()]+")
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")


@dataclass(frozen=True, slots=True)
class RedactionResult:
    text: str
    stripped_tokens: list[str]


class PIIRedactor:
    """Strips identity tokens before text reaches the scoring engine."""

    def redact(
        self, text: str, *, blind_mode: bool = False, full_name: str = ""
    ) -> RedactionResult:
        if not blind_mode:
            return RedactionResult(text, [])

        result = text
        stripped: list[str] = []

        def apply(pattern: re.Pattern[str], placeholder: str) -> None:
            nonlocal result
            stripped.extend(match.group(0) for match in pattern.finditer(result))
            result = pattern.sub(placeholder, result)

        apply(LINK_RE, "[URL]")
        apply(EMAIL_RE, "[EMAIL]")
        apply(PHONE_RE, "[PHONE]")
        if full_name.strip():
            apply(re.compile(re.escape(full_name), re.I), "[NAME]")
        apply(YEAR_RE, "[YEAR]")
        return RedactionResult(result, stripped)
