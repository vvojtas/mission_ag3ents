"""Shared path validation and workspace resolution helpers."""

from pathlib import Path


def resolve_workspace_path(workspace_root: Path, relative_path: str) -> Path:
    """Resolve a workspace-relative path and validate it stays within the workspace.

    Args:
        workspace_root: Absolute path to the workspace root.
        relative_path: User-provided relative path.

    Returns:
        Resolved absolute path.

    Raises:
        ValueError: If the resolved path escapes the workspace.
    """
    resolved = (workspace_root / relative_path).resolve()
    if not resolved.is_relative_to(workspace_root.resolve()):
        raise ValueError(
            f"Path '{relative_path}' resolves outside the workspace. "
            "Only paths within the workspace are allowed."
        )
    return resolved
