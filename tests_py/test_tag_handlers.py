from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

import yaml12


class CustomError(Exception):
    pass


def _apply_tag_handlers(obj: object, handlers: dict[str, object]):
    """Walk a parsed YAML tree and invoke handlers for tagged Yaml nodes."""
    if isinstance(obj, yaml12.Yaml):
        inner = _apply_tag_handlers(obj.value, handlers)
        tagged = yaml12.Yaml(inner, obj.tag)
        handler = handlers.get(obj.tag)
        return handler(tagged) if handler else tagged
    if isinstance(obj, list):
        return [_apply_tag_handlers(item, handlers) for item in obj]
    if isinstance(obj, dict):
        return {
            _apply_tag_handlers(k, handlers): _apply_tag_handlers(v, handlers)
            for k, v in obj.items()
        }
    return obj


def _assert_no_tagged(obj: object):
    if isinstance(obj, yaml12.Yaml):
        raise AssertionError(f"unexpected Yaml value: {obj}")
    if isinstance(obj, list):
        for item in obj:
            _assert_no_tagged(item)
    if isinstance(obj, dict):
        for k, v in obj.items():
            _assert_no_tagged(k)
            _assert_no_tagged(v)


def test_tag_handlers_transform_values_to_domain_types():
    text = """\
workdir: !path /srv/app
schedule:
  - !seconds 1.5
  - wait
  - !seconds 0.25
started_at: !ts 2024-11-22T18:30:00Z
"""
    handlers = {
        "!path": Path,
        "!seconds": lambda value: dt.timedelta(seconds=float(value)),
        "!ts": lambda value: dt.datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        ),
    }

    converted = yaml12.parse_yaml(text, handlers=handlers)

    _assert_no_tagged(converted)
    assert converted["workdir"] == Path("/srv/app")
    assert converted["schedule"][0] == dt.timedelta(seconds=1.5)
    assert converted["schedule"][1] == "wait"
    assert converted["schedule"][2] == dt.timedelta(seconds=0.25)
    assert converted["started_at"] == dt.datetime(
        2024, 11, 22, 18, 30, tzinfo=dt.timezone.utc
    )


def test_tag_handlers_update_keys_and_nested_structures():
    env = {"HOME": "/home/example", "CONF": "/etc/app.conf"}
    text = """\
? !env HOME
: {cfg: !env CONF}
paths:
  !path /tmp/output: done
"""
    handlers = {
        "!env": env.__getitem__,
        "!path": Path,
    }

    converted = yaml12.parse_yaml(text, handlers=handlers)

    _assert_no_tagged(converted)
    assert converted[env["HOME"]] == {"cfg": env["CONF"]}
    assert converted["paths"][Path("/tmp/output")] == "done"


def test_read_yaml_applies_handlers(tmp_path):
    path = tmp_path / "handler.yml"
    path.write_text("value: !upper foo", encoding="utf-8")
    handlers = {"!upper": lambda value: str(value).upper()}

    parsed = yaml12.read_yaml(str(path), handlers=handlers)

    _assert_no_tagged(parsed)
    assert parsed == {"value": "FOO"}


def test_manual_postprocessing_of_tagged_values_and_keys():
    env = {"HOME": "/home/example", "CONF": "/etc/app.conf"}
    text = """\
workdir: !path /srv/app
paths:
  !path /tmp/output: done
config:
  - !seconds 1.5
  - wait
  - !seconds 0.25
start_at: !ts 2024-11-22T18:30:00Z
? !env HOME
: !env CONF
"""
    raw = yaml12.parse_yaml(text)
    assert isinstance(raw["workdir"], yaml12.Yaml)
    assert any(isinstance(k, yaml12.Yaml) for k in raw["paths"].keys())
    assert isinstance(raw["config"][0], yaml12.Yaml)

    handlers = {
        "!path": lambda tagged: Path(tagged.value),
        "!seconds": lambda tagged: dt.timedelta(seconds=float(tagged.value)),
        "!ts": lambda tagged: dt.datetime.fromisoformat(
            str(tagged.value).replace("Z", "+00:00")
        ),
        "!env": lambda tagged: env[tagged.value],
    }

    converted = _apply_tag_handlers(raw, handlers)

    _assert_no_tagged(converted)
    assert converted["workdir"] == Path("/srv/app")
    assert converted["paths"][Path("/tmp/output")] == "done"
    assert converted["config"][0] == dt.timedelta(seconds=1.5)
    assert converted["config"][1] == "wait"
    assert converted["config"][2] == dt.timedelta(seconds=0.25)
    assert converted["start_at"] == dt.datetime(
        2024, 11, 22, 18, 30, tzinfo=dt.timezone.utc
    )
    assert converted[env["HOME"]] == env["CONF"]


def test_handler_exception_passes_through_for_value():
    def blow_up(tagged):
        raise CustomError("boom value")

    with pytest.raises(CustomError, match="boom value"):
        yaml12.parse_yaml("value: !boom 1", handlers={"!boom": blow_up})


def test_handler_exception_passes_through_for_key():
    def blow_up(tagged):
        raise CustomError("boom key")

    text = """\
? !boom key
: value
"""
    with pytest.raises(CustomError, match="boom key"):
        yaml12.parse_yaml(text, handlers={"!boom": blow_up})


def test_tagged_scalar_preserves_string_value():
    out = yaml12.parse_yaml("!foo 001")

    assert isinstance(out, yaml12.Yaml)
    assert out.tag == "!foo"
    assert out.value == "001"
    assert isinstance(out.value, str)


def test_non_specific_tag_scalar_returns_tagged_without_handler():
    out = yaml12.parse_yaml("! 001")

    assert isinstance(out, yaml12.Yaml)
    assert out.tag == "!"
    assert out.value == "001"
    assert isinstance(out.value, str)


def test_non_specific_tag_scalar_with_handler_overrides_value():
    calls = []

    def handle_non_specific(value):
        calls.append(value)
        return f"handled:{value}"

    out = yaml12.parse_yaml("! 001", handlers={"!": handle_non_specific})

    assert out == "handled:001"
    assert calls == ["001"]
    assert isinstance(calls[0], str)
