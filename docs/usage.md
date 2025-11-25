# Usage

The Python surface of `yaml12` is intentionally small: four functions that parse and emit YAML plus a single `Yaml` helper (also exported as `Tagged`/`MappingKey`) that you only need for two cases: tagged nodes and collection keys.

## Parse YAML text

Use `parse_yaml(text, multi=False, handlers=None)` when you already have YAML as a string. `text` accepts either a single string or a sequence of strings that will be joined with newlines. Empty input returns `None` (or `[]` when `multi=True`).

```python
from yaml12 import parse_yaml

config = parse_yaml("title: yaml12\nitems:\n  - rust\n  - python\n")
assert config["items"] == ["rust", "python"]
```

- Set `multi=True` to parse a stream of documents into a list; `multi=False` returns only the first document and ignores the rest of the stream.
- Supply `handlers` (a `dict` mapping tag strings to callables) to coerce specific tags on the fly. Handlers see already-parsed Python values and run for tagged keys as well as values. See [Custom Tags](tags.md) for details.
- Non-core tags without handlers become `Yaml(tag=..., value=...)`. Unhashable mapping keys (lists/dicts or tagged collections) become `Yaml(value, tag=None)` so they remain usable as dictionary keys; tagged scalar keys become `Yaml` with the tag preserved.

## Read from files

`read_yaml(path, multi=False, handlers=None)` reads YAML from disk and parses it with the same semantics as `parse_yaml`. `path` may be a string, a `pathlib.Path`/`os.PathLike`, or a file-like object with `.read()` that yields text or bytes. Streaming readers are fine; chunk sizes are handled internally.

```python
from yaml12 import read_yaml

settings = read_yaml("config.yml")
print(settings["debug"])
```

File I/O errors raise `IOError`. Parse problems surface as `ValueError`. Invalid handler definitions raise `TypeError`. Empty input returns `None` (or `[]` when `multi=True`).

## Emit YAML text

`format_yaml(value, multi=False)` serializes a Python value (or list of documents when `multi=True`) into YAML text. `Yaml` values retain their tags unless they target core scalar tags like `!!int` or `!!str`. Unhashable mapping keys stay wrapped in `Yaml(value, tag=None)`.

```python
from yaml12 import format_yaml

yaml_text = format_yaml({"env": "dev", "replicas": 2})
print(yaml_text)
# env: dev
# replicas: 2
```

When `multi=False`, the returned string omits a leading document marker and the trailing newline. When `multi=True`, the string starts with `---\n` and ends with `...\n`; passing an empty sequence emits `---\n...\n`. Non-sequences raise `TypeError` when `multi=True`.

## Write YAML to disk or stdout

`write_yaml(value, path=None, multi=False)` writes YAML straight to a file when `path` is provided or to stdout otherwise. `path` may be a string, a `pathlib.Path`/`os.PathLike`, or a writable object with `.write()`. Writers are tried with text first and retried as bytes if the text path fails.

```python
from yaml12 import write_yaml

write_yaml(["first", "second"], path="out.yml", multi=True)
# out.yml now contains:
# ---
# - first
# - second
# ...
```

`write_yaml` always wraps single-document output with `---\n` and closes it with `...\n` to make downstream stream parsing unambiguous; multi-document output also ends with `...\n`.

## Complex mapping keys

YAML allows sequences, mappings, and tagged scalars as keys. Parsed results wrap any unhashable key (collections or tagged collections) in `Yaml(value, tag=None)` so it can live in a Python `dict` while preserving equality and hashing by structure. Tagged scalar keys remain tagged `Yaml` nodes. To emit an unhashable key, wrap it in `Yaml` (for tagged collections, set `Yaml(value, tag)`), then pass it to `format_yaml` or `write_yaml`.

## Quick `Yaml` examples

```python
from yaml12 import Yaml, format_yaml, parse_yaml

# Tagged value
text = format_yaml({"mode": Yaml("prod", "!mode")})
assert parse_yaml(text)["mode"].tag == "!mode"

# Untagged collection key
mapping = {Yaml(["a", "b"]): "v"}
assert parse_yaml(format_yaml(mapping))[Yaml(["a", "b"])] == "v"

# Tagged collection key
mapping = {Yaml(["a", "b"], "!pair"): "v"}
key = next(iter(parse_yaml(format_yaml(mapping))))
assert key.tag == "!pair" and key.value == ["a", "b"]
```
