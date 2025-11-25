# Custom Tags

YAML 1.2 allows tagging values with custom semantics. `yaml12` preserves those tags by default and lets you plug in your own coercions.

## Yaml wrapper

Non-core tags that do not have a matching handler are wrapped in a frozen `Yaml` dataclass (also exported as `Tagged`):

```python
from yaml12 import Yaml, parse_yaml

color = parse_yaml("!color red")
assert isinstance(color, Yaml)
assert color.value == "red"
assert color.tag == "!color"
```

`Yaml` works for both scalar and collection nodes, including keys in mappings. You can serialize tagged values by passing a `Yaml` instance back into `format_yaml` or `write_yaml`. Non-specific tags (`!`) produce `Yaml("value", "!")` unless you supply a handler. Tagged scalar keys become `Yaml(value, tag)`; tagged collections and untagged collections used as keys are wrapped in `Yaml(value, tag)` (with `tag=None` for untagged collections).

Core scalar tags (`!!str`, `!!int`, `!!float`, `!!bool`, `!!null`, `!!seq`, `!!map`) are normalized to plain Python values instead of `Yaml`. Informative core tags (such as `!!timestamp`, `!!binary`, `!!set`, `!!omap`, or `!!pairs`) stay tagged so you can choose whether to handle them or preserve them verbatim. Invalid values for core tags raise `ValueError`.

## Handler functions

Provide a `handlers` dictionary to `parse_yaml` or `read_yaml` to intercept specific tags. Keys are tag strings (for example `"!point"` or `"tag:example.com,2024:point"`). Values are callables that receive the already-parsed value and return whatever Python object you want to substitute.

```python
from dataclasses import dataclass
from yaml12 import parse_yaml

@dataclass(frozen=True)
class Point:
    x: int
    y: int

def point_handler(value):
    # value is a regular Python mapping because the inner YAML was parsed first
    return Point(x=value["x"], y=value["y"])

doc = parse_yaml("vertex: !point\n  x: 1\n  y: 2\n", handlers={"!point": point_handler})
assert doc["vertex"] == Point(1, 2)
```

Handlers apply to both values and keys, including non-specific `!` tags if you include a `"!"` entry. If a handler raises an exception, it propagates as-is to help debugging.
