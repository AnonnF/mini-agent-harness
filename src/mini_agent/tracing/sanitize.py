DEFAULT_TRACE_OUTPUT_MAX_CHARS = 2000

_TRUNCATE_MARKER = "...[truncated]"


def truncate_text(text: str, *, max_chars: int) -> str:
    if max_chars < 1:
        raise ValueError("Max number of chars should be >= 1")

    if len(text) <= max_chars:
        return text

    if max_chars <= len(_TRUNCATE_MARKER):
        return _TRUNCATE_MARKER[:max_chars]

    keep = max_chars - len(_TRUNCATE_MARKER)
    return text[:keep] + _TRUNCATE_MARKER