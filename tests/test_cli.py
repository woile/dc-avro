import ast
import os
from unittest import mock

import pytest
from httpx import Response, codes
from typer.testing import CliRunner

from dc_avro._types import JsonDict, SerializationType
from dc_avro.main import app

runner = CliRunner()

url = "https://schema-registry/example.avsc"


def test_validate_schema_from_path(schema_dir: str):
    result = runner.invoke(
        app, ["validate-schema", "--path", os.path.join(schema_dir, "example.avsc")]
    )
    assert result.exit_code == 0
    assert "Valid schema!!" in result.stdout


def test_validate_schema_from_url(example_schema_json: JsonDict):
    response = Response(status_code=codes.OK, json=example_schema_json)
    with mock.patch("dc_avro.main._schema_utils.httpx.get", return_value=response):
        result = runner.invoke(app, ["validate-schema", "--url", url])
        assert result.exit_code == 0
        assert "Valid schema!!" in result.stdout


def test_validate_schema_invalid_path(schema_dir):
    result = runner.invoke(
        app,
        ["validate-schema", "--path", os.path.join(schema_dir, "invalid_example.avsc")],
    )
    assert result.exit_code == 1

    result = runner.invoke(
        app,
        ["validate-schema", "--url", "https://google.com"],
    )
    assert result.exit_code == 1


def test_invalid_schema_two_options(schema_dir: str):
    result = runner.invoke(
        app,
        [
            "validate-schema",
            "--path",
            os.path.join(schema_dir, "invalid_example.avsc"),
            "--url",
            "https://some.url",
        ],
    )
    assert result.exit_code == 2


def test_generate_model_from_path(schema_dir: str, model_generator_output_command: str):
    result = runner.invoke(
        app, ["generate-model", "--path", os.path.join(schema_dir, "example.avsc")]
    )
    assert result.exit_code == 0
    assert model_generator_output_command == result.stdout


def test_generate_model_from_url(
    example_schema_json: JsonDict, model_generator_output_command: str
):
    response = Response(status_code=codes.OK, json=example_schema_json)
    with mock.patch("dc_avro.main._schema_utils.httpx.get", return_value=response):
        result = runner.invoke(app, ["generate-model", "--url", url])
        assert result.exit_code == 0
        assert model_generator_output_command == result.stdout


def test_generate_model_two_options(schema_dir: str):
    result = runner.invoke(
        app,
        [
            "generate-model",
            "--path",
            os.path.join(schema_dir, "invalid_example.avsc"),
            "--url",
            "https://some.url",
        ],
    )
    assert result.exit_code == 2


@pytest.mark.parametrize(
    "expected_stdout, serialization_type",
    [
        (
            # This is the commend stdout, not the real serialization b'\x08bondd\x04\x06dog\x06cat\x00\x02\x06key\x02\x00\x00\x00\x12Argentina\x00u00ffffffffffffx'
            "b'\\x08bondd\\x04\\x06dog\\x06cat\\x00\\x02\\x06key\\x02\\x00\\x00\\x00\\x12Argentina\\x00u00\nffffffffffffx'\n",
            SerializationType.AVRO,
        ),
        (
            # This is the commend stdout, not the real serialization b'{"name": "bond", "age": 50, "pets": ["dog", "cat"], "accounts": {"key": 1}, "favorite_colors": "BLUE", "has_car": false, "country":  "Argentina", "address": null, "md5": "u00ffffffffffffx"}'
            'b\'{"name": "bond", "age": 50, "pets": ["dog", "cat"], "accounts": {"key": 1}, \n"favorite_colors": "BLUE", "has_car": false, "country": "Argentina", "address": \nnull, "md5": "u00ffffffffffffx"}\'\n',
            SerializationType.AVRO_JSON,
        ),
    ],
)
def test_serialize_from_path(
    schema_dir: str, expected_stdout: str, serialization_type: str
):
    data = "{'name': 'bond', 'age': 50, 'pets': ['dog', 'cat'], 'accounts': {'key': 1}, 'has_car': False, 'favorite_colors': 'BLUE', 'country': 'Argentina', 'address': None, 'md5': b'u00ffffffffffffx'}"

    result = runner.invoke(
        app,
        [
            "serialize",
            data,
            "--path",
            os.path.join(schema_dir, "example.avsc"),
            "--serialization-type",
            serialization_type,
        ],
    )
    assert expected_stdout == result.stdout


@pytest.mark.parametrize(
    "expected_stdout, serialization_type",
    [
        (
            # This is the commend stdout, not the real serialization b'\x08bondd\x04\x06dog\x06cat\x00\x02\x06key\x02\x00\x00\x00\x12Argentina\x00u00ffffffffffffx'
            "b'\\x08bondd\\x04\\x06dog\\x06cat\\x00\\x02\\x06key\\x02\\x00\\x00\\x00\\x12Argentina\\x00u00\nffffffffffffx'\n",
            SerializationType.AVRO,
        ),
        (
            # This is the commend stdout, not the real serialization b'{"name": "bond", "age": 50, "pets": ["dog", "cat"], "accounts": {"key": 1}, "favorite_colors": "BLUE", "has_car": false, "country":  "Argentina", "address": null, "md5": "u00ffffffffffffx"}'
            'b\'{"name": "bond", "age": 50, "pets": ["dog", "cat"], "accounts": {"key": 1}, \n"favorite_colors": "BLUE", "has_car": false, "country": "Argentina", "address": \nnull, "md5": "u00ffffffffffffx"}\'\n',
            SerializationType.AVRO_JSON,
        ),
    ],
)
def test_serialize_from_url(
    example_schema_json: JsonDict, expected_stdout: str, serialization_type: str
):
    data = "{'name': 'bond', 'age': 50, 'pets': ['dog', 'cat'], 'accounts': {'key': 1}, 'has_car': False, 'favorite_colors': 'BLUE', 'country': 'Argentina', 'address': None, 'md5': b'u00ffffffffffffx'}"

    response = Response(status_code=codes.OK, json=example_schema_json)
    with mock.patch("dc_avro.main._schema_utils.httpx.get", return_value=response):
        result = runner.invoke(
            app,
            [
                "serialize",
                data,
                "--url",
                url,
                "--serialization-type",
                serialization_type,
            ],
        )
        assert result.exit_code == 0
        assert expected_stdout == result.stdout


def test_serialize_two_options_invalid(schema_dir: str):
    result = runner.invoke(
        app,
        [
            "serialize",
            "{}",
            "--path",
            os.path.join(schema_dir, "invalid_example.avsc"),
            "--url",
            "https://some.url",
        ],
    )
    assert result.exit_code == 2


@pytest.mark.parametrize(
    "event, serialization_type",
    [
        # (
        #     'b"\x08bondd\x04\x06dog\x06cat\x00\x02\x06key\x02\x00\x00\x00\x12Argentina\x00u00ffffffffffffx"',
        #     SerializationType.AVRO,
        # ),
        (
            '{"name": "bond", "age": 50, "pets": ["dog", "cat"], "accounts": {"key": 1}, "favorite_colors": "BLUE", "has_car": false, "country":  "Argentina", "address": null, "md5": "u00ffffffffffffx"}',
            SerializationType.AVRO_JSON,
        ),
    ],
)
def test_deserialize_from_path(schema_dir: str, event: str, serialization_type: str):
    data = {
        "name": "bond",
        "age": 50,
        "pets": ["dog", "cat"],
        "accounts": {"key": 1},
        "has_car": False,
        "favorite_colors": "BLUE",
        "country": "Argentina",
        "address": None,
        "md5": b"u00ffffffffffffx",
    }
    result = runner.invoke(
        app,
        [
            "deserialize",
            event,
            "--path",
            os.path.join(schema_dir, "example.avsc"),
            "--serialization-type",
            serialization_type,
        ],
    )
    assert result.exit_code == 0
    assert data == ast.literal_eval(result.stdout)


@pytest.mark.parametrize(
    "event, serialization_type",
    [
        # (
        #     b"\x08bondd\x04\x06dog\x06cat\x00\x02\x06key\x02\x00\x00\x00\x12Argentina\x00u00ffffffffffffx",
        #     SerializationType.AVRO,
        # ),
        (
            b'{"name": "bond", "age": 50, "pets": ["dog", "cat"], "accounts": {"key": 1}, "favorite_colors": "BLUE", "has_car": false, "country":  "Argentina", "address": null, "md5": "u00ffffffffffffx"}',
            SerializationType.AVRO_JSON,
        ),
    ],
)
def test_deserialize_from_url(
    example_schema_json: JsonDict, event: bytes, serialization_type: str
):
    data = {
        "name": "bond",
        "age": 50,
        "pets": ["dog", "cat"],
        "accounts": {"key": 1},
        "has_car": False,
        "favorite_colors": "BLUE",
        "country": "Argentina",
        "address": None,
        "md5": b"u00ffffffffffffx",
    }

    response = Response(status_code=codes.OK, json=example_schema_json)
    with mock.patch("dc_avro.main._schema_utils.httpx.get", return_value=response):
        result = runner.invoke(
            app,
            [
                "deserialize",
                event,
                "--url",
                url,
                "--serialization-type",
                serialization_type,
            ],
        )
        assert result.exit_code == 0
        assert data == ast.literal_eval(result.stdout)


def test_deserialize_two_options_invalid(schema_dir: str):
    result = runner.invoke(
        app,
        [
            "deserialize",
            "{}",
            "--path",
            os.path.join(schema_dir, "invalid_example.avsc"),
            "--url",
            "https://some.url",
        ],
    )
    assert result.exit_code == 2


def test_lint_valid(schema_dir: str):
    result = runner.invoke(
        app,
        [
            "lint",
            os.path.join(schema_dir, "example.avsc"),
        ],
    )
    assert result.exit_code == 0


def test_lint_invalid_resource(schema_dir: str):
    result = runner.invoke(
        app,
        [
            "lint",
            os.path.join(schema_dir, "invalid_resource.txt"),
        ],
    )
    assert result.exit_code == 1


def test_lint_invalid_schema(schema_dir: str):
    result = runner.invoke(
        app,
        [
            "lint",
            os.path.join(schema_dir, "invalid_example.avsc"),
        ],
    )
    assert result.exit_code == 1


def test_generate_data_from_path(schema_dir: str):
    result = runner.invoke(
        app, ["generate-data", os.path.join(schema_dir, "example.avsc")]
    )
    assert result.exit_code == 0
