# yaml12

`yaml12` exposes the Rust-based `saphyr` YAML 1.2 parser and emitter to Python through a small, function-first API. The bindings keep conversions lean, support multi-document streams, and materialize tagged nodes or unhashable mapping keys as a single lightweight `Yaml` dataclass; otherwise you just use plain Python types.

- Parse YAML text or files into familiar Python types with `parse_yaml` and `read_yaml`; handlers apply to both values and keys.
- Serialize Python values back to YAML with `format_yaml` or write directly to disk/stdout with `write_yaml`, including non-core tags.
- Round-trip tagged nodes and unhashable mapping keys using `Yaml`, keeping tagged scalars, tagged collections, and bare collections stable across parse/format.

## Installation

The project targets Python 3.10+ and builds via `maturin` (Rust toolchain required). From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e . --no-build-isolation
```

## Quick start

```python
from yaml12 import parse_yaml, format_yaml

yaml_text = """
title: A modern YAML parser and emitter written in Rust
properties: [fast, correct, safe, simple]
features:
  tags: preserve
  streams: multi
"""

doc = parse_yaml(yaml_text)

assert doc == {
    "title": "A modern YAML parser and emitter written in Rust",
    "properties": ["fast", "correct", "safe", "simple"],
    "features": {"tags": "preserve", "streams": "multi"},
}

text = format_yaml(doc)
print(text)
# title: A modern YAML parser and emitter written in Rust
# properties:
#   - fast
#   - correct
#   - safe
#   - simple
# features:
#   tags: preserve
#   streams: multi
```

### Reading and writing files

```python
from yaml12 import read_yaml, write_yaml

value_out = {"alpha": 1, "nested": [True, None]}

write_yaml(value_out, "my.yaml")
value_in = read_yaml("my.yaml")

assert value_in == value_out

# Multi-document streams
docs_out = [{"foo": 1}, {"bar": [2, None]}]

write_yaml(docs_out, "my-multi.yaml", multi=True)
docs_in = read_yaml("my-multi.yaml", multi=True)

assert docs_in == docs_out
```

### Tag handlers

Handlers let you opt into custom behaviour for tagged nodes while keeping the default parser strict and safe.

```python
from yaml12 import parse_yaml

yaml_text = """
- !upper [rust, python]
- !expr 6 * 7
"""

handlers = {
    "!expr": lambda value: eval(value),
    "!upper": str.upper,
}

doc = parse_yaml(yaml_text, handlers=handlers)
assert doc == [["RUST", "PYTHON"], 42]
```

### Formatting and round-tripping

```python
from yaml12 import Yaml, format_yaml, parse_yaml

obj = {
    "seq": [1, 2],
    "map": {"key": "value"},
    "tagged": Yaml("1 + 1", "!expr"),
}

yaml_text = format_yaml(obj)
print(yaml_text)
# seq:
#   - 1
#   - 2
# map:
#   key: value
# tagged: !expr 1 + 1

parsed = parse_yaml(yaml_text)
assert parsed == {
    "seq": [1, 2],
    "map": {"key": "value"},
    "tagged": Yaml("1 + 1", "!expr"),
}
```

## Where to go next

- Learn YAML essentials in [YAML in 2 Minutes](usage.md).
- Explore tags, anchors, and advanced features in [Tags, Anchors, and Advanced YAML](tags.md).
- Scan the callable surface in [API Reference](api.md).

## Build or serve the docs locally

Install MkDocs if you have not already:

```bash
python -m pip install mkdocs
```

Then from the project root:

```bash
# Build static site into ./site
.venv/bin/mkdocs build

# Serve with live reload at http://127.0.0.1:8000
.venv/bin/mkdocs serve
```
