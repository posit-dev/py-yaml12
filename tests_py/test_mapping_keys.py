from __future__ import annotations

import yaml12


def test_sequence_key_returns_mapping_key():
    result = yaml12.parse_yaml("? [a, b, c]\n: 1\n")

    key = next(iter(result))
    assert isinstance(key, yaml12.MappingKey)
    assert key.value == ["a", "b", "c"]
    assert list(key) == ["a", "b", "c"]
    assert key[1] == "b"
    assert len(key) == 3
    assert result[yaml12.MappingKey(["a", "b", "c"])] == 1


def test_mapping_key_returns_mapping_key():
    result = yaml12.parse_yaml("? {foo: 1, bar: [2]}\n: value\n")

    key = next(iter(result))
    assert isinstance(key, yaml12.MappingKey)
    assert isinstance(key.value, dict)
    assert key.value["foo"] == 1
    assert key["foo"] == 1
    assert list(key) == ["foo", "bar"]
    assert result[yaml12.MappingKey({"foo": 1, "bar": [2]})] == "value"


def test_scalar_keys_remain_plain_types():
    parsed = yaml12.parse_yaml("foo: 1\n2: bar")

    assert parsed["foo"] == 1
    assert parsed[2] == "bar"
    assert not any(isinstance(k, yaml12.MappingKey) for k in parsed)


def test_handler_returning_mapping_is_wrapped():
    text = "? !wrap foo\n: bar"
    handlers = {"!wrap": lambda value: {"key": value}}

    parsed = yaml12.parse_yaml(text, handlers=handlers)
    key = next(iter(parsed))

    assert isinstance(key, yaml12.MappingKey)
    assert key.value == {"key": "foo"}
    assert parsed[yaml12.MappingKey({"key": "foo"})] == "bar"


def test_mapping_key_round_trip_format_and_parse():
    key = yaml12.MappingKey({"foo": [1, 2]})
    original = {key: "value"}

    encoded = yaml12.format_yaml(original)
    reparsed = yaml12.parse_yaml(encoded)
    reparsed_key = next(iter(reparsed))

    assert isinstance(reparsed_key, yaml12.MappingKey)
    assert reparsed_key.value == {"foo": [1, 2]}
    assert reparsed == {yaml12.MappingKey({"foo": [1, 2]}): "value"}
    assert reparsed == original


def test_mapping_key_with_tagged_mapping_proxies_inner_value():
    parsed = yaml12.parse_yaml("? !foo {bar: 1}\n: baz\n")
    key = next(iter(parsed))

    assert isinstance(key, yaml12.MappingKey)
    assert isinstance(key.value, yaml12.Tagged)
    assert key.value.tag == "!foo"
    assert key.value.value == {"bar": 1}
    assert key["bar"] == 1
    assert list(key) == ["bar"]
    assert parsed[yaml12.MappingKey(key.value)] == "baz"


def test_mapping_key_hashes_by_structure():
    k1 = yaml12.MappingKey({"b": 2, "a": 1})
    k2 = yaml12.MappingKey({"a": 1, "b": 2})

    assert k1 == k2
    assert hash(k1) == hash(k2)


def test_collection_values_stay_plain():
    parsed = yaml12.parse_yaml(
        "top:\n"
        "  - [1, 2]\n"
        "  - {foo: bar}\n"
    )

    items = parsed["top"]
    assert items[0] == [1, 2]
    assert isinstance(items[1], dict)
    assert not any(isinstance(k, yaml12.MappingKey) for k in items[1])
