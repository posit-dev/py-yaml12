# yaml12

`yaml12` exposes the Rust-based `saphyr` YAML 1.2 parser and emitter to Python through a small, function-first API. The bindings keep conversions lean, support multi-document streams, and materialize tagged nodes or unhashable mapping keys as a single lightweight `Yaml` dataclass (also exported as `Tagged` and `MappingKey`); otherwise you just use plain Python types.

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

doc = parse_yaml("server:\\n  port: 8000\\n  debug: true")
assert doc == {"server": {"port": 8000, "debug": True}}

text = format_yaml(doc)
print(text)
# server:
#   port: 8000
#   debug: true
```

Multi-document streams are just as simple:

```python
docs = parse_yaml(["first: 1", "second: 2"], multi=True)
assert docs == [{"first": 1}, {"second": 2}]
```

## Where to go next

- Learn how to parse and emit YAML in more detail in [Usage](usage.md).
- See how to work with custom tags and handlers in [Custom Tags](tags.md).
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
