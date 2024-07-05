import json
import pytest
from json_loader_with_include.json_loader import JSONLoaderWithInclude


@pytest.fixture
def loader():
    return JSONLoaderWithInclude


@pytest.mark.parametrize("input_data, expected", [
    ({"foo": "bar", "hello": "world"}, {"foo": "bar", "hello": "world"}),
    ({"foo": "bar", "array": [1, 2, 3]}, {"foo": "bar", "array": [1, 2, 3]}),
    ({"key1": "value1", "key2": 2, "key3": [1, 2, 3]}, {"key1": "value1", "key2": 2, "key3": [1, 2, 3]}),
    ({"key": {"subkey": "subvalue"}}, {"key": {"subkey": "subvalue"}}),
    ([{"foo": "bar"}, {"hello": "world"}], [{"foo": "bar"}, {"hello": "world"}]),
    ([{"foo": "bar"}, {"array": [1, 2, 3]}], [{"foo": "bar"}, {"array": [1, 2, 3]}]),
    ([{"key1": "value1"}, {"key2": 2}, {"key3": [1, 2, 3]}], [{"key1": "value1"}, {"key2": 2}, {"key3": [1, 2, 3]}]),
    ([{"key": {"subkey": "subvalue"}}], [{"key": {"subkey": "subvalue"}}]),
])
def test_process_data_basic(loader, input_data, expected):
    assert loader._process_data(input_data, "") == expected


def test_process_data_include_whole_external_file(loader, tmpdir):
    p = tmpdir.mkdir("sub").join("hello.json")
    p.write('{"included_key": "included_value"}')
    data = {"foo": "bar", "include": {"filename": str(p)}}
    expected = {"foo": "bar", "included_key": "included_value"}
    assert loader._process_data(data, p) == expected


def test_process_data_include_list_of_whole_external_files(loader, tmpdir):
    p1 = tmpdir.mkdir("sub1").join("hello1.json")
    p1.write('{"included_key1": "included_value1"}')
    p2 = tmpdir.mkdir("sub2").join("hello2.json")
    p2.write('{"included_key2": "included_value2"}')
    data = {"foo": "bar", "include": [{"filename": str(p1)}, {"filename": str(p2)}]}
    expected = {"foo": "bar", "included_key1": "included_value1", "included_key2": "included_value2"}
    assert loader._process_data(data, "") == expected


def test_process_data_include_external_file_dict_data_based_on_keys(loader, tmpdir):
    """Testing the logic circle when the main data structure is a dictionary with 'include' key
    pointing to another JSON file with specific 'keys' to be included."""
    p = tmpdir.mkdir("sub").join("hello.json")
    p.write('{"included_key": "included_value", "not_included_key": "value"}')
    data = {"foo": "bar", "include": {"filename": str(p), "keys": ["included_key"]}}
    expected = {"foo": "bar", "included_key": "included_value"}
    assert loader._process_data(data, p) == expected


def test_process_data_include_external_file_list_data_based_on_keys(loader, tmpdir):
    """Testing the logic when the main data structure is a list where one of its elements is a dictionary
    with an 'include' condition with 'keys' information."""
    p = tmpdir.mkdir("sub").join("json_with_list.json")
    p.write(json.dumps([{"ext": "val"}, {"array": [1, 2, 3]}]))
    input_data = [
        {"foo": "bar"},
        [],
        {"include": {
            "filename": str(p),
            "keys": [0, 1]
        }}
    ]
    expected = [
        {"foo": "bar"},
        [],
        {"ext": "val"},
        {"array": [1, 2, 3]}
    ]

    assert loader._process_data(input_data, p) == expected


def test_process_data_include_nested_external_file(loader, tmpdir):
    # Create an external file structure with nested data
    p = tmpdir.mkdir("sub").join("nested.json")
    p.write(json.dumps({"level1": {"level2": {"included_key": "included_value"}}}))

    # Define input data with keys_path to navigate nested structure
    data = {"foo": "bar", "include": {"filename": str(p), "keys_path": ["level1", "level2", "included_key"]}}
    expected = {"foo": "bar", "included_key": "included_value"}

    assert loader._process_data(data, p) == expected


def test_process_data_replace_value_with_single_key(loader, tmpdir):
    # Create an external file with data to be replaced
    p = tmpdir.mkdir("sub").join("replace.json")
    p.write(json.dumps({"included_key": "included_value", "other_key": "other_value"}))

    # Define input data using replace_value to replace current value
    data = {"foo": {"replace_value": {"filename": str(p), "key": "included_key"}}}
    expected = {"foo": "included_value"}

    assert loader._process_data(data, p) == expected


def test_process_data_replace_value_with_multiple_keys(loader, tmpdir):
    # Create an external file with multiple keys to be merged
    p = tmpdir.mkdir("sub").join("replace_multiple.json")
    p.write(json.dumps({"key1": {"param1": "value1"}, "key2": {"param2": "value2"}}))

    # Define input data using replace_value to replace current value with merged keys
    data = {"foo": {"replace_value": {"filename": str(p), "keys": ["key1", "key2"]}}}
    expected = {"foo": {"key1": {"param1": "value1"}, "key2": {"param2": "value2"}}}

    assert loader._process_data(data, p) == expected


def test_process_data_replace_value_with_keys_path(loader, tmpdir):
    # Create an external file with nested data to be replaced
    p = tmpdir.mkdir("sub").join("replace_nested.json")
    p.write(json.dumps({
        "level1": {
            "level2": {
                "data_key": "data_value",
                "other_key": "other_value"
            }
        }
    }))

    # Define input data using replace_value with keys_path to navigate nested structure and replace current value
    data = {
        "foo": {
            "replace_value": {
                "filename": str(p),
                "keys_path": ["level1", "level2", "data_key"]
            }
        }
    }
    expected = {"foo": "data_value"}

    assert loader._process_data(data, p) == expected
