from typing import Any

from pydantic import BaseModel


def inline_refs(node: Any, defs: dict[str, Any]) -> Any:
    """Recursively resolve ``$ref`` pointers against a ``$defs`` map."""
    if isinstance(node, dict):
        if "$ref" in node:
            ref_name = node["$ref"].split("/")[-1]
            return inline_refs(defs[ref_name], defs)
        return {k: inline_refs(v, defs) for k, v in node.items()}
    if isinstance(node, list):
        return [inline_refs(item, defs) for item in node]
    return node


def make_strict_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Recursively add ``additionalProperties: false`` to every object node.

    OpenAI strict mode requires this on every object in the schema tree.
    """
    if not isinstance(schema, dict):
        return schema
    schema = dict(schema)
    if schema.get("type") == "object":
        schema["additionalProperties"] = False
        if "properties" in schema:
            schema["properties"] = {
                k: make_strict_schema(v) for k, v in schema["properties"].items()
            }
    elif schema.get("type") == "array" and "items" in schema:
        schema["items"] = make_strict_schema(schema["items"])
    return schema


def clean_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Inline ``$ref``s, strip Pydantic metadata, and apply strict mode."""
    schema = inline_refs(schema, schema.get("$defs", {}))
    schema.pop("$defs", None)
    schema.pop("title", None)
    return make_strict_schema(schema)


def pydantic_to_strict_schema(model_cls: type[BaseModel]) -> dict[str, Any]:
    """Convert a Pydantic model class to an OpenAI-compatible strict JSON schema."""
    return clean_schema(model_cls.model_json_schema())
