from __future__ import annotations

from . import yaml12 as _native
from ._yaml import Yaml as Yaml

Yaml.__module__ = __name__

_native._set_yaml_class(Yaml)
_native.Yaml = Yaml

__version__ = _native.__version__
parse_yaml = _native.parse_yaml
read_yaml = _native.read_yaml
format_yaml = _native.format_yaml
write_yaml = _native.write_yaml
_dbg_yaml = _native._dbg_yaml
_normalize_tag = _native._normalize_tag

__all__ = [
    "__version__",
    "parse_yaml",
    "read_yaml",
    "format_yaml",
    "write_yaml",
    "_normalize_tag",
    "_dbg_yaml",
    "Yaml",
]

__doc__ = _native.__doc__

del _native

