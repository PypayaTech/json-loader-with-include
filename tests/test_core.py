import json
import pytest
from pypaya_json.core import PypayaJSON


@pytest.fixture
def loader():
    return PypayaJSON()


@pytest.fixture
def loader_with_comments():
    return PypayaJSON(comment_string="#")


@pytest.fixture
def loader_custom_enable_key():
    return PypayaJSON(enable_key="active")


@pytest.fixture
def loader_with_paths():
    """Loader with path annotations enabled (default)."""
    return PypayaJSON(resolve_path_annotations=True)


@pytest.fixture
def loader_without_paths():
    """Loader with path annotations disabled."""
    return PypayaJSON(resolve_path_annotations=False)


@pytest.fixture
def loader_custom_prefix():
    """Loader with custom path annotation prefix."""
    return PypayaJSON(path_annotation_prefix="$resolve:")


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


def test_process_data_include_nested_external_file_string_path(loader, tmpdir):
    p = tmpdir.mkdir("sub").join("nested.json")
    p.write(json.dumps({"level1": {"level2": {"included_key": "included_value"}}}))

    data = {"foo": "bar", "include": {"filename": str(p), "keys_path": "level1/level2/included_key"}}
    expected = {"foo": "bar", "included_key": "included_value"}

    assert loader._process_data(data, p) == expected


def test_process_data_include_nested_external_file_list_path(loader, tmpdir):
    p = tmpdir.mkdir("sub").join("nested.json")
    p.write(json.dumps({"level1": {"level2": {"included_key": "included_value"}}}))

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
                "keys_path": "level1/level2/data_key"
            }
        }
    }
    expected = {"foo": "data_value"}

    assert loader._process_data(data, p) == expected


def test_process_data_include_nested_keys_string_path(loader, tmpdir):
    p = tmpdir.mkdir("sub").join("nested_keys.json")
    p.write(json.dumps({
        "level1": {
            "level2": {
                "key1": "value1",
                "key2": "value2"
            }
        }
    }))

    data = {
        "include": {
            "filename": str(p),
            "keys": ["level1/level2/key1", "level1/level2/key2"]
        }
    }
    expected = {
        "key1": "value1",
        "key2": "value2"
    }

    assert loader._process_data(data, p) == expected


def test_process_data_include_nested_keys_list_path(loader, tmpdir):
    p = tmpdir.mkdir("sub").join("nested_keys.json")
    p.write(json.dumps({
        "level1": {
            "level2": {
                "key1": "value1",
                "key2": "value2"
            }
        }
    }))

    data = {
        "include": {
            "filename": str(p),
            "keys": [["level1", "level2", "key1"], ["level1", "level2", "key2"]]
        }
    }
    expected = {
        "key1": "value1",
        "key2": "value2"
    }

    assert loader._process_data(data, p) == expected


def test_process_data_include_nested_keys_mixed_format(loader, tmpdir):
    p = tmpdir.mkdir("sub").join("nested_keys.json")
    p.write(json.dumps({
        "level1": {
            "level2": {
                "key1": "value1",
                "key2": "value2"
            }
        },
        "level3": {
            "key3": "value3"
        }
    }))

    data = {
        "include": {
            "filename": str(p),
            "keys": ["level1/level2/key1", ["level1", "level2", "key2"], "level3/key3"]
        }
    }
    expected = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }

    assert loader._process_data(data, p) == expected


def test_process_data_with_disabled_item(loader, tmpdir):
    p = tmpdir.mkdir("sub").join("hello.json")
    p.write('{"included_key": "included_value"}')
    data = {
        "foo": "bar",
        "include": {
            "enabled": False,
            "filename": str(p)
        },
        "baz": "qux"
    }
    expected = {"foo": "bar", "baz": "qux"}
    assert loader._process_data(data, str(tmpdir)) == expected


def test_process_data_with_nested_disabled_item(loader, tmpdir):
    p = tmpdir.mkdir("sub").join("hello.json")
    p.write('{"included_key": "included_value"}')
    data = {
        "foo": "bar",
        "nested": {
            "include": {
                "enabled": False,
                "filename": str(p)
            }
        },
        "baz": "qux"
    }
    expected = {"foo": "bar", "nested": {}, "baz": "qux"}
    assert loader._process_data(data, str(tmpdir)) == expected


def test_process_data_with_custom_enable_key(loader_custom_enable_key, tmpdir):
    p = tmpdir.mkdir("sub").join("hello.json")
    p.write('{"included_key": "included_value"}')
    data = {
        "foo": "bar",
        "include": {
            "active": True,
            "filename": str(p)
        },
        "baz": "qux"
    }
    expected = {"foo": "bar", "included_key": "included_value", "baz": "qux"}
    assert loader_custom_enable_key._process_data(data, str(tmpdir)) == expected


def test_process_data_with_comments(loader_with_comments, tmpdir):
    p = tmpdir.mkdir("sub").join("hello.json")
    p.write('''
    {
        "key1": "value1",
        # This is a comment
        # "key2": "value2",
        "key3": "value3"
    }
    ''')
    data = {"include": {"filename": str(p)}}
    expected = {"key1": "value1", "key3": "value3"}
    assert loader_with_comments._process_data(data, str(tmpdir)) == expected


def test_process_data_with_disabled_list_item(loader, tmpdir):
    p1 = tmpdir.mkdir("sub1").join("file1.json")
    p1.write('{"key1": "value1"}')
    p2 = tmpdir.mkdir("sub2").join("file2.json")
    p2.write('{"key2": "value2"}')
    data = {
        "include": [
            {"filename": str(p1)},
            {"enabled": False, "filename": str(p2)}
        ]
    }
    expected = {"key1": "value1"}
    assert loader._process_data(data, str(tmpdir)) == expected


def test_process_data_with_all_disabled_items(loader, tmpdir):
    p = tmpdir.mkdir("sub").join("hello.json")
    p.write('{"included_key": "included_value"}')
    data = {
        "foo": {"enabled": False, "value": "bar"},
        "include": {"enabled": False, "filename": str(p)},
        "baz": {"enabled": False, "value": "qux"}
    }
    expected = {}
    assert loader._process_data(data, str(tmpdir)) == expected


def test_path_annotation_basic(loader_with_paths, tmpdir):
    """Test basic path annotation resolution."""
    data = {
        "@path:data_dir": "subdir/data",
        "regular_field": "value"
    }

    result = loader_with_paths._process_data(data, str(tmpdir))

    expected_path = str(tmpdir.join("subdir", "data"))
    assert result["data_dir"] == expected_path
    assert result["regular_field"] == "value"
    assert "@path:data_dir" not in result


def test_path_annotation_nested(loader_with_paths, tmpdir):
    """Test path annotations in nested structures."""
    data = {
        "config": {
            "@path:checkpoint_path": "models/best.ckpt",
            "@path:data_dir": "subdir/data"  # Use simple relative path
        },
        "other": "value"
    }

    result = loader_with_paths._process_data(data, str(tmpdir))

    expected_checkpoint = str(tmpdir.join("models", "best.ckpt"))
    expected_data = str(tmpdir.join("subdir", "data"))

    assert result["config"]["checkpoint_path"] == expected_checkpoint
    assert result["config"]["data_dir"] == expected_data
    assert result["other"] == "value"
    assert "@path:checkpoint_path" not in result["config"]
    assert "@path:data_dir" not in result["config"]


def test_path_annotation_in_list(loader_with_paths, tmpdir):
    """Test path annotations within list structures."""
    data = [
        {"@path:file1": "dir1/file.txt"},
        {"regular": "value"},
        {"@path:file2": "dir2/file.txt"}
    ]

    result = loader_with_paths._process_data(data, str(tmpdir))

    expected_file1 = str(tmpdir.join("dir1", "file.txt"))
    expected_file2 = str(tmpdir.join("dir2", "file.txt"))

    assert result[0]["file1"] == expected_file1
    assert result[1]["regular"] == "value"
    assert result[2]["file2"] == expected_file2


def test_path_annotation_absolute_path(loader_with_paths, tmpdir):
    """Test that absolute paths are preserved."""
    import os
    absolute_path = os.path.abspath("/some/absolute/path")

    data = {"@path:abs_path": absolute_path}
    result = loader_with_paths._process_data(data, str(tmpdir))

    # Should still be absolute, but resolved
    assert os.path.isabs(result["abs_path"])
    assert result["abs_path"] == absolute_path


def test_path_annotation_disabled(loader_without_paths, tmpdir):
    """Test that path annotations are ignored when disabled."""
    data = {
        "@path:data_dir": "subdir/data",
        "regular_field": "value"
    }

    result = loader_without_paths._process_data(data, str(tmpdir))

    # Should remain unchanged
    assert result == data
    assert "@path:data_dir" in result


def test_path_annotation_custom_prefix(loader_custom_prefix, tmpdir):
    """Test custom path annotation prefix."""
    data = {
        "$resolve:data_dir": "subdir/data",
        "@path:not_resolved": "should/not/change"
    }

    result = loader_custom_prefix._process_data(data, str(tmpdir))

    expected_path = str(tmpdir.join("subdir", "data"))
    assert result["data_dir"] == expected_path
    assert result["@path:not_resolved"] == "should/not/change"
    assert "$resolve:data_dir" not in result


def test_path_annotation_empty_string(loader_with_paths, tmpdir):
    """Test handling of empty path strings."""
    data = {"@path:empty_path": ""}
    result = loader_with_paths._process_data(data, str(tmpdir))

    assert result["empty_path"] == ""


def test_path_annotation_non_string_value(loader_with_paths, tmpdir):
    """Test that non-string values with path prefix are ignored."""
    data = {
        "@path:valid_path": "subdir/data",
        "@path:invalid_number": 123,
        "@path:invalid_dict": {"nested": "value"}
    }

    result = loader_with_paths._process_data(data, str(tmpdir))

    expected_path = str(tmpdir.join("subdir", "data"))
    assert result["valid_path"] == expected_path
    # Non-string values should be preserved as-is
    assert result["@path:invalid_number"] == 123
    assert result["@path:invalid_dict"] == {"nested": "value"}


def test_path_annotation_with_includes(loader_with_paths, tmpdir):
    """Test path annotations combined with includes."""
    # Create external file
    external_file = tmpdir.join("external.json")
    external_file.write(json.dumps({"@path:external_path": "external/data"}))

    data = {
        "@path:local_path": "local/data",
        "include": {"filename": str(external_file)}
    }

    result = loader_with_paths._process_data(data, str(tmpdir))

    expected_local = str(tmpdir.join("local", "data"))
    expected_external = str(tmpdir.join("external", "data"))

    assert result["local_path"] == expected_local
    assert result["external_path"] == expected_external


def test_has_path_annotations_detection(loader_with_paths):
    """Test the _has_path_annotations optimization method."""
    # Data with path annotations
    data_with_paths = {"@path:test": "value", "regular": "value"}
    assert loader_with_paths._has_path_annotations(data_with_paths) is True

    # Data without path annotations
    data_without_paths = {"regular": "value", "other": "value"}
    assert loader_with_paths._has_path_annotations(data_without_paths) is False

    # Nested data with path annotations
    nested_data = {"level1": {"@path:nested": "value"}}
    assert loader_with_paths._has_path_annotations(nested_data) is True

    # List with path annotations
    list_data = [{"@path:item": "value"}]
    assert loader_with_paths._has_path_annotations(list_data) is True


def test_path_annotation_class_method(tmpdir):
    """Test path annotations using the class method."""
    config_file = tmpdir.join("config.json")
    data = {
        "@path:data_dir": "subdir/data",
        "regular_field": "value"
    }
    config_file.write(json.dumps(data))

    result = PypayaJSON.load(
        str(config_file),
        resolve_path_annotations=True
    )

    expected_path = str(tmpdir.join("subdir", "data"))
    assert result["data_dir"] == expected_path
    assert result["regular_field"] == "value"


def test_path_annotation_prefix_validation():
    """Test validation of path annotation prefix."""
    # Valid prefix
    loader = PypayaJSON(path_annotation_prefix="@custom:")
    assert loader.path_annotation_prefix == "@custom:"

    # Invalid prefix - empty string
    with pytest.raises(ValueError, match="path_annotation_prefix cannot be empty"):
        PypayaJSON(path_annotation_prefix="")

    # Invalid prefix - not a string
    with pytest.raises(ValueError, match="path_annotation_prefix must be a string"):
        PypayaJSON(path_annotation_prefix=123)


def test_path_annotation_complex_nested_structure(loader_with_paths, tmpdir):
    """Test path annotations in complex nested structures."""
    data = {
        "training": {
            "@path:data_dir": "data/training",
            "model": {
                "@path:checkpoint": "models/best.ckpt"
            }
        },
        "inference": {
            "@path:model_path": "models/inference.ckpt"
        },
        "callbacks": [
            {
                "type": "ModelCheckpoint",
                "@path:dirpath": "outputs/checkpoints"
            },
            {
                "type": "Logger",
                "@path:save_dir": "outputs/logs"
            }
        ]
    }

    result = loader_with_paths._process_data(data, str(tmpdir))

    # Check all paths were resolved
    assert result["training"]["data_dir"] == str(tmpdir.join("data", "training"))
    assert result["training"]["model"]["checkpoint"] == str(tmpdir.join("models", "best.ckpt"))
    assert result["inference"]["model_path"] == str(tmpdir.join("models", "inference.ckpt"))
    assert result["callbacks"][0]["dirpath"] == str(tmpdir.join("outputs", "checkpoints"))
    assert result["callbacks"][1]["save_dir"] == str(tmpdir.join("outputs", "logs"))

    # Check no annotation keys remain
    assert "@path:data_dir" not in result["training"]
    assert "@path:checkpoint" not in result["training"]["model"]
    assert "@path:model_path" not in result["inference"]
    assert "@path:dirpath" not in result["callbacks"][0]
    assert "@path:save_dir" not in result["callbacks"][1]
