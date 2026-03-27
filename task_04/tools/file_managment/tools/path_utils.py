"""Shared path validation and workspace resolution helpers."""

from pathlib import Path

_BINARY_EXTENSIONS = frozenset({
    ".exe", ".dll", ".so", ".dylib", ".bin", ".dat",
    ".zip", ".gz", ".tar", ".bz2", ".7z", ".rar",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".svg",
    ".mp3", ".mp4", ".avi", ".mov", ".wav", ".flac",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".pyc", ".pyo", ".class", ".o", ".obj",
    ".woff", ".woff2", ".ttf", ".eot",
    ".db", ".sqlite", ".sqlite3",
})

_SKIP_DIRS = frozenset({
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox",
    "dist", "build", "egg-info",
})


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


def is_likely_binary(path: Path) -> bool:
    """Heuristic check: is the file likely binary based on extension?"""
    return path.suffix.lower() in _BINARY_EXTENSIONS


def should_skip_dir(name: str) -> bool:
    """Return True for directories that should be excluded from listings/searches."""
    return name in _SKIP_DIRS or name.endswith(".egg-info")


def iter_text_files(workspace_root: Path) -> list[Path]:
    """Collect all non-binary files under the workspace, skipping ignored dirs.

    Returns workspace-relative Path objects, sorted alphabetically.
    """
    results: list[Path] = []
    root = workspace_root.resolve()

    def _walk(directory: Path) -> None:
        try:
            entries = sorted(directory.iterdir())
        except PermissionError:
            return
        for entry in entries:
            if entry.is_dir():
                if not should_skip_dir(entry.name):
                    _walk(entry)
            elif entry.is_file() and not is_likely_binary(entry):
                results.append(entry.relative_to(root))

    _walk(root)
    return results
