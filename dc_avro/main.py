import ast
from typing import Dict, List, Optional

import rich
import typer
from dataclasses_avroschema import BaseClassEnum, ModelGenerator, serialization
from deepdiff import DeepDiff

from . import _schema_utils
from ._types import JsonDict, SerializationType
from .exceptions import InvalidSchema, JsonRequired

app = typer.Typer()
console = rich.console.Console()


def generate_error_messages(
    path_name: Optional[str] = "--path", url_name: Optional[str] = "--url"
) -> Dict[str, str]:
    return {
        "all_specified": f"You can not specify both {path_name} and {url_name}",
        "required": f"{path_name} or {url_name} must be specified",
    }


def get_resource(
    *,
    path: Optional[str] = None,
    url: Optional[str] = None,
    error_messages: Optional[Dict[str, str]] = None,
) -> JsonDict:
    error_messages = error_messages or generate_error_messages()

    if all([path, url]):
        raise typer.BadParameter(error_messages["all_specified"])
    elif path is not None:
        return _schema_utils.get_resource_from_path(path=path)
    elif url is not None:
        return _schema_utils.get_resource_from_url(url=url)
    else:
        raise typer.BadParameter(error_messages["required"])


@app.command()
def generate_model(
    path: str = typer.Option(None),
    url: str = typer.Option(None),
    base_class: BaseClassEnum = typer.Option(
        BaseClassEnum.AVRO_MODEL,
        help="Model base class",
    ),
):
    resource = get_resource(path=path, url=url)
    _schema_utils.validate(schema=resource)

    model_generator = ModelGenerator(base_class=base_class.value)
    result = model_generator.render(schema=resource)

    print(result)


@app.command()
def schema_diff(
    source_path: str = typer.Option(None, help="Source path to the local schema"),
    source_url: str = typer.Option(None, help="Source schema url"),
    target_path: str = typer.Option(None, help="Target path to the local schema"),
    target_url: str = typer.Option(None, help="Target schema url"),
):
    source_resource = get_resource(
        path=source_path,
        url=source_url,
        error_messages=generate_error_messages(
            path_name="--source-path", url_name="--source-url"
        ),
    )
    target_resource = get_resource(
        path=target_path,
        url=target_url,
        error_messages=generate_error_messages(
            path_name="--path-path", url_name="--path-url"
        ),
    )
    _schema_utils.validate(schema=source_resource)
    _schema_utils.validate(schema=target_resource)

    console.print(DeepDiff(source_resource, target_resource))


@app.command()
def serialize(
    data: str = typer.Argument(None, callback=ast.literal_eval),
    path: str = typer.Option(None),
    url: str = typer.Option(None),
    serialization_type: SerializationType = typer.Option(
        SerializationType.AVRO,
    ),
):
    resource = get_resource(path=path, url=url)
    _schema_utils.validate(schema=resource)

    output = serialization.serialize(
        data, resource, serialization_type=serialization_type  # type: ignore
    )
    console.print(output)


@app.command()
def deserialize(
    event: str,
    path: str = typer.Option(None),
    url: str = typer.Option(None),
    serialization_type: SerializationType = typer.Option(
        SerializationType.AVRO,
    ),
):
    resource = get_resource(path=path, url=url)
    _schema_utils.validate(schema=resource)

    data = (
        ast.literal_eval(event)
        if serialization_type == SerializationType.AVRO.value
        else event.encode()
    )
    output = serialization.deserialize(
        data, resource, serialization_type=serialization_type
    )
    console.print(output)


@app.command()
def validate_schema(
    path: Optional[str] = typer.Option(None, help="Path to the local schema"),
    url: Optional[str] = typer.Option(None, help="Schema url"),
):
    resource = get_resource(path=path, url=url)

    if _schema_utils.validate(schema=resource):
        console.print("[bold green]Valid schema!![/bold green] :+1: \n")
        console.print(resource)


@app.command()
def lint(files: List[str]) -> None:
    errors: dict = {}
    valid_schemas = []
    for path in files:
        try:
            schema = _schema_utils.get_resource_from_path(path=path)
        except JsonRequired as e:
            errors[path] = e
            continue
        try:
            _schema_utils.validate(schema=schema)
        except InvalidSchema as e:
            errors[path] = e
            continue
        valid_schemas.append(path)
    if valid_schemas:
        console.print(f"\n:+1: Total valid schemas: {len(valid_schemas)}")
        for valid in valid_schemas:
            console.print(valid)
    if errors:
        error_msg = f"Total errors detected: {len(errors.keys())}"
        for error_path, error in errors.items():
            console.print(":boom: File: " + error_path)
            console.print(f"[red]{error}[/red]")
        app.pretty_exceptions_show_locals = False
        raise InvalidSchema(error_msg)


@app.command(help="Generate fake data for a given avsc schema")
def generate_data(
    resource: str = typer.Argument(None, help="Path or URL to the avro schema"),
    count: int = typer.Option(
        1, help="Number of data to generate, more than one prints a list"
    ),
):
    schema = _schema_utils.get_schema(resource=resource)
    data = _schema_utils.generate_data(schema=schema, count=count)
    console.print(data)
