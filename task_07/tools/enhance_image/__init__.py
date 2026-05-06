"""Enhance image MCP server package."""

__all__ = ["create_enhance_image_mcp", "mcp"]


def __getattr__(name: str):
    if name in __all__:
        from . import server as _server

        return getattr(_server, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
