"""Versioned schema registry for graceful API schema evolution."""
from datetime import datetime
from typing import Any

SCHEMAS = {
    "default": {
        "version": "1.0",
        "fields": {
            "id": {"type": "string", "required": True},
            "name": {"type": "string", "required": True},
            "email": {"type": "string", "required": False},
            "created_at": {"type": "datetime", "required": False},
            "updated_at": {"type": "datetime", "required": False},
        }
    }
}

class SchemaRegistry:
    def __init__(self):
        self.schemas = SCHEMAS.copy()

    def register(self, source_name: str, schema: dict):
        self.schemas[source_name] = schema

    def get(self, source_name: str) -> dict:
        return self.schemas.get(source_name, self.schemas["default"])

    def validate(self, source_name: str, record: dict) -> list:
        schema = self.get(source_name)
        errors = []
        for field_name, field_spec in schema.get("fields", {}).items():
            if field_spec.get("required") and field_name not in record:
                errors.append(f"Missing required field: {field_name}")
        return errors

    def transform(self, source_name: str, record: dict) -> dict:
        schema = self.get(source_name)
        result = {"_source": source_name, "_schema_version": schema["version"]}
        for field_name, field_spec in schema.get("fields", {}).items():
            if field_name in record:
                value = record[field_name]
                if field_spec["type"] == "datetime" and isinstance(value, str):
                    try:
                        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except ValueError:
                        value = None
                result[field_name] = value
        result["_raw"] = record
        return result

registry = SchemaRegistry()