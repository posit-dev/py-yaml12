from __future__ import annotations

import io
import sys
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from os import PathLike
from typing import Any, Literal, Protocol, TypeVar, overload

__all__: list[str]

@dataclass(frozen=True)
class Yaml:
    """Tagged node or hashable wrapper for unhashable mapping keys."""

    value: Any
    tag: str | None = ...

    def __post_init__(self) -> None: ...

    def __getitem__(self, key: Any, /) -> Any: ...
    def __iter__(self) -> Any: ...
    def __len__(self) -> int: ...


@overload
def parse_yaml(
    text: str | Iterable[str],
    multi: Literal[False] = False,
    handlers: Mapping[str, Callable[[Any], Any]] | None = None,
) -> Any: ...


@overload
def parse_yaml(
    text: str | Iterable[str],
    multi: Literal[True],
    handlers: Mapping[str, Callable[[Any], Any]] | None = None,
) -> list[Any]: ...

if sys.version_info >= (3, 14):
    @overload
    def read_yaml(
        path: str | PathLike[str] | io.Reader[str] | io.Reader[bytes],
        multi: Literal[False] = False,
        handlers: Mapping[str, Callable[[Any], Any]] | None = None,
    ) -> Any: ...

    @overload
    def read_yaml(
        path: str | PathLike[str] | io.Reader[str] | io.Reader[bytes],
        multi: Literal[True],
        handlers: Mapping[str, Callable[[Any], Any]] | None = None,
    ) -> list[Any]: ...

    def _dbg_yaml(text: str | Iterable[str] | io.Reader[str] | io.Reader[bytes]) -> None: ...

    def write_yaml(
        value: Any,
        path: str | PathLike[str] | io.Writer[str] | None = None,
        multi: bool = False,
    ) -> None: ...
else:
    _T_co = TypeVar("_T_co", covariant=True)

    class _Reader(Protocol[_T_co]):
        def read(self, size: int = ..., /) -> _T_co: ...

    class _Writer(Protocol):
        def write(self, data: str, /) -> int: ...

    @overload
    def read_yaml(
        path: str | PathLike[str] | _Reader[str] | _Reader[bytes],
        multi: Literal[False] = False,
        handlers: Mapping[str, Callable[[Any], Any]] | None = None,
    ) -> Any: ...

    @overload
    def read_yaml(
        path: str | PathLike[str] | _Reader[str] | _Reader[bytes],
        multi: Literal[True],
        handlers: Mapping[str, Callable[[Any], Any]] | None = None,
    ) -> list[Any]: ...

    def _dbg_yaml(text: str | Iterable[str] | _Reader[str] | _Reader[bytes]) -> None: ...

    def write_yaml(
        value: Any,
        path: str | PathLike[str] | _Writer | None = None,
        multi: bool = False,
    ) -> None: ...


def format_yaml(value: Any, multi: bool = False) -> str: ...


__version__: str
