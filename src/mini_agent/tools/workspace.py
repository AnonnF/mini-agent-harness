from pathlib import Path

from mini_agent.exceptions import ToolExecutionError

SENSITIVE_NAMES = {".env", "id_rsa", "id_ed25519", ".env.local"}


def resolve_in_workspace(root: Path, user_path: str) -> Path:
    normalized = user_path.strip() or "."

    resolved_root = root.resolve()
    candidate = (resolved_root / normalized).resolve()

    if not candidate.is_relative_to(resolved_root):
        raise ToolExecutionError(f"Path escapes workspace root: {user_path!r}")
    if candidate.name in SENSITIVE_NAMES:
        raise ToolExecutionError(f"Sensitive path denied: {user_path!r}")

    return candidate
