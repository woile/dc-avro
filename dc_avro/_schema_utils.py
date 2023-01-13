import json

import httpx
from fastavro import _schema_common, parse_schema

from .exceptions import InvalidSchema, JsonRequired
from .types import JsonDict


def get_resource_from_url(url: str) -> str:
    try:
        response = httpx.get(url)
        return response.json()
    except json.JSONDecodeError as exc:
        raise JsonRequired(f"Can not convert to json the resource from {url}") from exc


def get_resource_from_path(path: str) -> str:
    with open(path, mode="r") as resource:
        schema = resource.read()
        try:
            return json.loads(schema)
        except json.JSONDecodeError as exc:
            raise JsonRequired(
                f"Can not convert to json the resource from {path}"
            ) from exc


def validate_schema(schema: JsonDict) -> bool:
    try:
        parse_schema(schema=schema)
        return True
    except _schema_common.SchemaParseException as exc:
        raise InvalidSchema(
            f"Schema {schema} is not valid.\n Error: `{str(exc)}`"
        ) from exc
    except _schema_common.UnknownType as exc:
        raise InvalidSchema(
            f"Schema {schema} is an unknown type.\n Make sure that its type is a python dictionary"
        ) from exc
