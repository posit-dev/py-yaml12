from __future__ import annotations

import collections.abc as _abc
from dataclasses import dataclass
import typing as _typing

if _typing.TYPE_CHECKING:

    def _normalize_tag(tag: str) -> str: ...

else:
    from .yaml12 import _normalize_tag


def _freeze(obj: object) -> object:
    if isinstance(obj, Yaml):
        return ("yaml", obj.tag, _freeze(obj.value))
    if isinstance(obj, _abc.Mapping):
        return ("map", tuple((_freeze(k), _freeze(v)) for k, v in obj.items()))
    if isinstance(obj, _abc.Sequence) and not isinstance(obj, (str, bytes, bytearray)):
        return ("seq", tuple(_freeze(x) for x in obj))
    try:
        hash(obj)
        return obj
    except TypeError:
        return ("unhashable", id(obj))


@dataclass(frozen=True)
class Yaml:
    """Tagged node or hashable wrapper for unhashable mapping keys."""

    value: _typing.Any
    tag: str | None = None

    def __post_init__(self) -> None:
        tag = self.tag
        if isinstance(tag, str):
            normalized = _normalize_tag(tag)
            if normalized != tag:
                object.__setattr__(self, "tag", normalized)
        frozen = ("tagged", self.tag, _freeze(self.value))
        object.__setattr__(self, "_frozen", frozen)
        object.__setattr__(self, "_hash", hash(frozen))

    def __hash__(self) -> int:
        return _typing.cast(int, getattr(self, "_hash"))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Yaml):
            return NotImplemented
        return _typing.cast(object, getattr(self, "_frozen")) == _typing.cast(
            object, getattr(other, "_frozen")
        )

    def _proxy_target(self) -> object | None:
        target = self.value.value if isinstance(self.value, Yaml) else self.value
        if isinstance(target, (_abc.Mapping, _abc.Sequence)) and not isinstance(
            target, (str, bytes, bytearray)
        ):
            return target
        return None

    def __getitem__(self, key: object) -> object:
        target = self._proxy_target()
        if target is not None:
            return target[key]  # type: ignore[index]
        raise TypeError("Yaml.value does not support indexing")

    def __iter__(self):
        target = self._proxy_target()
        if target is not None:
            return iter(target)
        raise TypeError("Yaml.value is not iterable")

    def __len__(self) -> int:
        target = self._proxy_target()
        if target is not None:
            return len(target)  # type: ignore[arg-type]
        raise TypeError("Yaml.value has no len()")

    def __repr__(self) -> str:
        if self.tag is None:
            return f"Yaml({self.value!r})"
        return f"Yaml(value={self.value!r}, tag={self.tag!r})"
