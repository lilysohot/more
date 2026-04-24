import json
import re
from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError

TModel = TypeVar("TModel", bound=BaseModel)


class StructuredOutputParseError(ValueError):
    """Raised when LLM output cannot be parsed into expected structured data."""


def extract_json_text(raw_text: str) -> str:
    """Extract a valid JSON substring from LLM raw output."""
    text = (raw_text or "").strip()
    if not text:
        raise StructuredOutputParseError("LLM output is empty")

    candidates = _build_candidates(text)
    for candidate in candidates:
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            continue

    raise StructuredOutputParseError("No valid JSON payload found in LLM output")


def parse_model_response(raw_text: str, model_cls: Type[TModel]) -> TModel:
    """Parse LLM output JSON and validate with a Pydantic model class."""
    json_text = extract_json_text(raw_text)

    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise StructuredOutputParseError(f"JSON decode failed: {exc.msg}") from exc

    try:
        return model_cls.model_validate(payload)
    except ValidationError as exc:
        raise StructuredOutputParseError(f"Schema validation failed: {exc}") from exc


def _build_candidates(text: str) -> list[str]:
    candidates: list[str] = []

    fenced_blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
    for block in fenced_blocks:
        block_text = block.strip()
        if block_text:
            candidates.append(block_text)

    candidates.append(text)

    clipped = _clip_bracketed_json(text)
    if clipped and clipped not in candidates:
        candidates.append(clipped)

    return candidates


def _clip_bracketed_json(text: str) -> str:
    starts = [idx for idx in (text.find("{"), text.find("[")) if idx != -1]
    if not starts:
        return ""

    start = min(starts)
    end_curly = text.rfind("}")
    end_square = text.rfind("]")
    end = max(end_curly, end_square)

    if end <= start:
        return ""

    return text[start : end + 1].strip()
