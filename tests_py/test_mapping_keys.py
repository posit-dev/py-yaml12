from __future__ import annotations

import textwrap
from collections.abc import Mapping, Sequence

import pytest
import yaml12


def test_sequence_key_returns_mapping_key():
    result = yaml12.parse_yaml("? [a, b, c]\n: 1\n")

    key = next(iter(result))
    assert isinstance(key, yaml12.Yaml)
    assert key.value == ["a", "b", "c"]
    assert list(key) == ["a", "b", "c"]
    assert key[1] == "b"
    assert len(key) == 3
    assert result[yaml12.Yaml(["a", "b", "c"])] == 1


def test_mapping_key_returns_mapping_key():
    result = yaml12.parse_yaml("? {foo: 1, bar: [2]}\n: value\n")

    key = next(iter(result))
    assert isinstance(key, yaml12.Yaml)
    assert isinstance(key.value, dict)
    assert key.value["foo"] == 1
    assert key["foo"] == 1
    assert list(key) == ["foo", "bar"]
    assert result[yaml12.Yaml({"foo": 1, "bar": [2]})] == "value"


def test_scalar_keys_remain_plain_types():
    parsed = yaml12.parse_yaml("foo: 1\n2: bar")

    assert parsed["foo"] == 1
    assert parsed[2] == "bar"
    assert not any(isinstance(k, yaml12.Yaml) for k in parsed)


def test_handler_returning_mapping_is_wrapped():
    text = "? !wrap foo\n: bar"
    handlers = {"!wrap": lambda value: {"key": value}}

    parsed = yaml12.parse_yaml(text, handlers=handlers)
    key = next(iter(parsed))

    assert isinstance(key, yaml12.Yaml)
    assert key.value == {"key": "foo"}
    assert parsed[yaml12.Yaml({"key": "foo"})] == "bar"


def test_mapping_key_round_trip_format_and_parse():
    key = yaml12.Yaml({"foo": [1, 2]})
    original = {key: "value"}

    encoded = yaml12.format_yaml(original)
    reparsed = yaml12.parse_yaml(encoded)
    reparsed_key = next(iter(reparsed))

    assert isinstance(reparsed_key, yaml12.Yaml)
    assert reparsed_key.value == {"foo": [1, 2]}
    assert reparsed == {yaml12.Yaml({"foo": [1, 2]}): "value"}
    assert reparsed == original


def test_mapping_key_with_tagged_mapping_proxies_inner_value():
    parsed = yaml12.parse_yaml("? !foo {bar: 1}\n: baz\n")
    key = next(iter(parsed))

    assert isinstance(key, yaml12.Yaml)
    assert key.tag == "!foo"
    assert isinstance(key.value, dict)
    assert key.value["bar"] == 1
    assert key["bar"] == 1
    assert list(key) == ["bar"]
    assert parsed[yaml12.Yaml(key.value, "!foo")] == "baz"


def test_mapping_key_hashes_by_insertion_order():
    k1 = yaml12.Yaml({"b": 2, "a": 1})
    k2 = yaml12.Yaml({"a": 1, "b": 2})

    assert k1 != k2

    mapping = {k1: "value"}
    assert mapping[k1] == "value"
    with pytest.raises(KeyError):
        _ = mapping[k2]


def test_mapping_key_with_tagged_value_hashes_and_compares():
    k1 = yaml12.Yaml({"a": 1}, "!tag")
    k2 = yaml12.Yaml({"a": 1}, "!tag")

    assert k1 == k2
    assert hash(k1) == hash(k2)

    mapping = {k1: "value"}
    assert mapping[k2] == "value"


def test_mapping_key_tagged_round_trip_format_and_parse():
    key = yaml12.Yaml("foo", "!k")
    original = {key: "v"}

    encoded = yaml12.format_yaml(original)
    reparsed = yaml12.parse_yaml(encoded)
    reparsed_key = next(iter(reparsed))

    assert isinstance(reparsed_key, yaml12.Yaml)
    assert reparsed_key.tag == "!k"
    assert reparsed_key.value == "foo"
    assert reparsed == {yaml12.Yaml("foo", "!k"): "v"}


def test_collection_values_stay_plain():
    parsed = yaml12.parse_yaml("top:\n  - [1, 2]\n  - {foo: bar}\n")

    items = parsed["top"]
    assert items[0] == [1, 2]
    assert isinstance(items[1], dict)
    assert not any(isinstance(k, yaml12.Yaml) for k in items[1])


def test_tagged_outer_mapping_with_tagged_keys_round_trip():
    yaml_text = "!outer\n!k1 foo: 1\n!k2 bar: 2\n"

    parsed = yaml12.parse_yaml(yaml_text)
    assert isinstance(parsed, yaml12.Yaml)
    assert parsed.tag == "!outer"
    assert isinstance(parsed.value, dict)
    keys = list(parsed.value.keys())
    assert all(isinstance(k, yaml12.Yaml) for k in keys)
    assert {k.tag for k in keys} == {"!k1", "!k2"}
    assert parsed.value[keys[0]] in (1, 2)

    encoded = yaml12.format_yaml(parsed)
    reparsed = yaml12.parse_yaml(encoded)
    assert reparsed == parsed


def test_complex_tagged_and_untagged_mapping_keys_round_trip():
    yaml_text = textwrap.dedent(
        """\
        ? [a, b]
        : plain-seq
        ? {foo: bar}
        : !val {x: 1}
        ? !tagged-key scalar
        : [3, 4]
        ? tagged_value_key
        : !tagged-seq [5, 6]
        """
    )

    parsed = yaml12.parse_yaml(yaml_text)
    assert isinstance(parsed, dict)
    assert len(parsed) == 4

    keys = list(parsed.keys())
    assert any(isinstance(k, yaml12.Yaml) for k in keys)

    seq_key = yaml12.Yaml(["a", "b"])
    map_key = yaml12.Yaml({"foo": "bar"})
    tagged_scalar_key = yaml12.Yaml("scalar", "!tagged-key")
    plain_scalar_key = "tagged_value_key"

    assert parsed[seq_key] == "plain-seq"
    assert isinstance(parsed[map_key], yaml12.Yaml)
    assert parsed[map_key].tag == "!val"
    assert parsed[map_key].value == {"x": 1}
    assert parsed[tagged_scalar_key] == [3, 4]
    tagged_value = parsed[plain_scalar_key]
    assert isinstance(tagged_value, yaml12.Yaml)
    assert tagged_value.tag == "!tagged-seq"
    assert tagged_value.value == [5, 6]

    encoded = yaml12.format_yaml(parsed)
    reparsed = yaml12.parse_yaml(encoded)
    assert reparsed == parsed


def test_tagged_scalar_mapping_key_remains_tagged():
    parsed = yaml12.parse_yaml("!tag key: value\n")

    key = next(iter(parsed))
    assert isinstance(key, yaml12.Yaml)
    assert key.tag == "!tag"
    assert key.value == "key"
    assert parsed[key] == "value"


def test_other_yaml_node_types_on_keys():
    # Alias nodes never reach mapping_to_py (resolved earlier), but BadValue/Representation
    # should not cause wrapping; they are resolved or error before this stage.
    # Use a plain scalar to ensure the default branch remains unwrapped.
    parsed = yaml12.parse_yaml("plain: 1")
    assert "plain" in parsed


def test_mapping_key_handler_hash_error_wraps_once():
    class HashError:
        def __init__(self):
            self.calls = 0

        def __hash__(self):
            self.calls += 1
            raise TypeError("hash boom")

    holder: dict[str, HashError] = {}

    def handler(value):
        obj = HashError()
        holder["obj"] = obj
        return obj

    with pytest.raises(TypeError, match="hash boom"):
        yaml12.parse_yaml("? !hash key\n: value\n", handlers={"!hash": handler})

    assert holder["obj"].calls == 1


def test_mapping_key_handler_hash_attr_checked_once():
    counters: dict[str, int] = {"hash_attr_calls": 0, "hash_calls": 0}

    def make_obj():
        class HashAttrCounter:
            def __getattribute__(self, name):
                if name == "__hash__":
                    counters["hash_attr_calls"] += 1
                return object.__getattribute__(self, name)

            def __hash__(self):
                counters["hash_calls"] += 1
                return 123

        return HashAttrCounter()

    holder: dict[str, HashAttrCounter] = {}

    def handler(value: object) -> HashAttrCounter:  # noqa: ARG001
        obj = make_obj()
        holder["obj"] = obj
        return obj

    parsed = yaml12.parse_yaml("? !hash key\n: value\n", handlers={"!hash": handler})
    key = next(iter(parsed))

    assert holder["obj"] is key
    assert counters["hash_attr_calls"] == 1
    assert counters["hash_calls"] == 1
    assert parsed[key] == "value"


def test_tagged_collection_mapping_key_wraps_with_mapping_key():
    parsed = yaml12.parse_yaml("? !seq [a, b]\n: val\n")

    key = next(iter(parsed))
    assert isinstance(key, yaml12.Yaml)
    assert key.tag == "!seq"
    assert key.value == ["a", "b"]
    assert parsed[yaml12.Yaml(["a", "b"], "!seq")] == "val"


def test_handler_mapping_key_returns_unhashable_mapping_wrapped():
    class UnhashableMapping(Mapping):
        __hash__ = None

        def __init__(self, value):
            self._data = {"value": value}

        def __iter__(self):
            return iter(self._data)

        def __len__(self):
            return len(self._data)

        def __getitem__(self, key):
            return self._data[key]

    handlers = {"!wrap": lambda value: UnhashableMapping(value)}

    parsed = yaml12.parse_yaml("? !wrap key\n: v\n", handlers=handlers)
    key = next(iter(parsed))

    assert isinstance(key, yaml12.Yaml)
    assert isinstance(key.value, UnhashableMapping)
    assert parsed[yaml12.Yaml(UnhashableMapping("key"))] == "v"


class _HashlessSequence(Sequence):
    __hash__ = None

    def __init__(self, value):
        self._items = list(value)

    def __getitem__(self, idx):
        return self._items[idx]

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)


def test_handler_sequence_key_with_disabled_hash_is_wrapped():
    text = "? !wrap [a, b]\n: v\n"
    handlers = {"!wrap": lambda value: _HashlessSequence(value)}

    parsed = yaml12.parse_yaml(text, handlers=handlers)
    key = next(iter(parsed))

    assert isinstance(key, yaml12.Yaml)
    assert isinstance(key.value, _HashlessSequence)
    assert parsed[key] == "v"


def test_mapping_key_hash_error_propagates_once():
    class HashError:
        def __init__(self):
            self.calls = 0

        def __hash__(self):
            self.calls += 1
            raise TypeError("hash boom")

    holder: dict[str, object] = {}

    def handler(value: object) -> object:  # noqa: ARG001
        obj = HashError()
        holder["obj"] = obj
        return obj

    with pytest.raises(TypeError, match="hash boom"):
        yaml12.parse_yaml("? !hash key\n: value\n", handlers={"!hash": handler})

    assert holder["obj"].calls == 1


def test_mapping_key_handler_returns_unhashable_wrapped_once():
    class Unhashable:
        __hash__ = None

        def __init__(self, value):
            self.value = value

    def handler(val):
        return Unhashable(val)

    parsed = yaml12.parse_yaml("? !wrap key\n: value\n", handlers={"!wrap": handler})
    key = next(iter(parsed))
    assert isinstance(key, yaml12.Yaml)
    assert isinstance(key.value, Unhashable)
    assert parsed[key] == "value"


def test_yaml_key_wraps_object_whose_hash_raises():
    class HashBoom:
        def __init__(self):
            self.calls = 0

        def __hash__(self):
            self.calls += 1
            raise TypeError("no hash")

    obj = HashBoom()
    key = yaml12.Yaml(obj)

    assert isinstance(key, yaml12.Yaml)
    assert obj.calls == 1  # probed once during Yaml hash computation

    mapping = {key: "value"}
    assert mapping[key] == "value"
    assert obj.calls == 1
