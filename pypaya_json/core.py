import json
import os
from typing import Optional, Any, Dict, List, Union
from pathlib import Path


class PypayaJSON:
    """Enhanced JSON processing with includes, comments, and path resolution."""

    def __init__(self,
                 enable_key: str = "enabled",
                 comment_string: Optional[str] = None,
                 resolve_path_annotations: bool = True,
                 path_annotation_prefix: str = "@path:"):
        """
        Initialize PypayaJSON with enhanced processing capabilities.

        Args:
            enable_key (str): The key used to enable or disable inclusions. Defaults to "enabled".
            comment_string (Optional[str]): The string used to denote comments in JSON files. Defaults to None.
            resolve_path_annotations (bool): Whether to resolve path annotations to absolute paths. Defaults to True.
            path_annotation_prefix (str): Prefix for path annotation keys. Keys starting with this prefix
                will have their values resolved to absolute paths. Defaults to "@path:".
                Examples: "@path:data_dir" -> {"data_dir": "/absolute/path/to/data"}
        """
        self.enable_key = enable_key
        self.comment_string = comment_string
        self.resolve_path_annotations = resolve_path_annotations

        if not isinstance(path_annotation_prefix, str):
            raise ValueError("path_annotation_prefix must be a string")
        if not path_annotation_prefix:
            raise ValueError("path_annotation_prefix cannot be empty (risk of conflicts)")
        self.path_annotation_prefix = path_annotation_prefix

    @classmethod
    def load(cls, path: str,
             enable_key: str = "enabled",
             comment_string: Optional[str] = None,
             resolve_path_annotations: bool = True,
             path_annotation_prefix: str = "@path:") -> Dict[str, Any]:
        """
        Load a JSON file with includes (one-time usage).

        Args:
            path (str): The path to the JSON file.
            enable_key (str): The key used to enable or disable inclusions. Defaults to "enabled".
            comment_string (Optional[str]): The string used to denote comments in JSON files. Defaults to None.
            resolve_path_annotations (bool): Whether to resolve path annotations. Defaults to True.
            path_annotation_prefix (str): Prefix for path annotation keys. Defaults to "@path:".

        Returns:
            Dict[str, Any]: The processed JSON data.
        """
        instance = cls(enable_key, comment_string, resolve_path_annotations, path_annotation_prefix)
        return instance.load_file(path)

    def load_file(self, path: str) -> Dict[str, Any]:
        """
        Load a JSON file using this instance's configuration.

        Args:
            path (str): The path to the JSON file.

        Returns:
            Dict[str, Any]: The processed JSON data.
        """
        with open(path, 'r') as f:
            if self.comment_string:
                # Remove comments before parsing
                data = self._remove_comments(f.read())
                json_data = json.loads(data)
            else:
                json_data = json.load(f)
        base_dir = os.path.dirname(path)
        return self._process_data(json_data, base_dir)

    def _remove_comments(self, json_string: str) -> str:
        """Remove comments from JSON string."""
        lines = json_string.split('\n')
        return '\n'.join(line.split(self.comment_string)[0].rstrip() for line in lines)

    def load_from_spec(self, spec: Dict[str, Any], base_dir: str) -> Any:
        """Load data from a file specified in the 'spec' dictionary."""
        full_path = os.path.join(base_dir, spec["filename"])
        data = self.load_file(full_path)

        # Navigate to nested keys if keys_path is present
        if "keys_path" in spec:
            keys = spec["keys_path"]
            if isinstance(keys, str):
                keys = keys.split('/')
            for key in keys:
                data = data[key]

        if "keys" in spec:
            if isinstance(data, list):
                data = [data[i] for i in spec["keys"]]
            elif isinstance(data, dict):
                data = {self._get_last_key(k): self._navigate_nested_key(data, k) for k in spec["keys"]}

        return data

    def _get_last_key(self, key: Union[str, List[str]]) -> str:
        """Get the last key from a nested key path."""
        if isinstance(key, str):
            return key.split('/')[-1]
        elif isinstance(key, list):
            return key[-1]
        return key

    def _navigate_nested_key(self, data: Dict[str, Any], key: Union[str, List[str]]) -> Any:
        """Navigate to a nested key in the data structure."""
        if isinstance(key, str):
            keys = key.split('/')
        elif isinstance(key, list):
            keys = key
        else:
            return data[key]  # If it's neither string nor list, treat it as a direct key

        for k in keys:
            data = data[k]
        return data

    def _is_enabled(self, data: Any) -> bool:
        """Check if a data element is enabled according to the enable_key."""
        return not isinstance(data, dict) or self.enable_key not in data or data[self.enable_key]

    def _handle_enabled_flag(self, data: Any) -> Any:
        """Filter data based on enabled flags."""
        if isinstance(data, dict):
            return {k: self._handle_enabled_flag(v) for k, v in data.items() if self._is_enabled(v)}
        elif isinstance(data, list):
            return [self._handle_enabled_flag(item) for item in data if self._is_enabled(item)]
        return data

    def _has_path_annotations(self, obj: Any) -> bool:
        """Quick check to determine if path annotation processing is needed."""
        if isinstance(obj, dict):
            return any(k.startswith(self.path_annotation_prefix) for k in obj.keys()) or \
                any(self._has_path_annotations(v) for v in obj.values()
                    if isinstance(v, (dict, list)))
        elif isinstance(obj, list):
            return any(self._has_path_annotations(item) for item in obj
                       if isinstance(item, (dict, list)))
        return False

    def _resolve_path_annotations(self, data: Any, base_dir: str) -> Any:
        """Resolve @path: annotations to absolute paths."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if key.startswith(self.path_annotation_prefix) and isinstance(value, str):
                    # This is a path annotation - resolve it
                    actual_key = key[len(self.path_annotation_prefix):]
                    resolved_path = self._resolve_single_path(value, base_dir)
                    result[actual_key] = resolved_path
                elif isinstance(value, (dict, list)):
                    # Recurse into nested structures
                    result[key] = self._resolve_path_annotations(value, base_dir)
                else:
                    # Regular key-value pair
                    result[key] = value
            return result
        elif isinstance(data, list):
            return [self._resolve_path_annotations(item, base_dir) for item in data]
        else:
            return data

    def _resolve_single_path(self, path_str: str, base_dir: str) -> str:
        """Resolve a single path string relative to base_dir."""
        if not path_str:
            return path_str

        path = Path(path_str)

        # If relative, make it relative to base_dir (same logic as includes)
        if not path.is_absolute():
            path = Path(base_dir) / path

        return str(path.expanduser().resolve())

    def _process_data(self, data: Any, base_dir: str) -> Any:
        """Process data, handling includes, replacements, path annotations, and nested structures."""
        # Handle enabled flag before processing
        data = self._handle_enabled_flag(data)

        # Handle path annotations if enabled and present
        if self.resolve_path_annotations and self._has_path_annotations(data):
            data = self._resolve_path_annotations(data, base_dir)

        if isinstance(data, list):
            new_data = []
            for i, v in enumerate(data):
                if isinstance(v, dict) and "include" in v:
                    included_data = self.load_from_spec(v["include"], base_dir)
                    if isinstance(included_data, list):
                        new_data.extend(included_data)
                    else:
                        new_data.append(included_data)
                elif isinstance(v, dict):
                    new_data.append(self._process_data(v, base_dir))
                else:
                    new_data.append(data[i])
            return new_data

        elif isinstance(data, dict):
            if "include" in data:
                if isinstance(data["include"], dict):
                    included_data = self.load_from_spec(data["include"], base_dir)
                    if isinstance(included_data, dict):
                        data.update(included_data)
                    else:
                        # Insert included data into the main dictionary key positions
                        key_path = data["include"].get("keys_path", "")
                        if isinstance(key_path, str):
                            key_path = key_path.split('/')
                        elif not isinstance(key_path, list):
                            key_path = []
                        if key_path:
                            last_key = key_path[-1]
                            data[last_key] = included_data
                        else:
                            data["included"] = included_data  # Default to 'included' key

                elif isinstance(data["include"], list):
                    for inc in data["include"]:
                        included_data = self.load_from_spec(inc, base_dir)
                        if isinstance(included_data, dict):
                            data.update(included_data)
                        else:
                            data["included"] = included_data  # Default to 'included' key
                del data["include"]

            if "replace_value" in data:
                replace_spec = data["replace_value"]
                replaced_data = self.load_from_spec(replace_spec, base_dir)
                if "keys" in replace_spec:
                    return {k: self._navigate_nested_key(replaced_data, k) for k in replace_spec["keys"]}
                if "key" in replace_spec:
                    return self._navigate_nested_key(replaced_data, replace_spec["key"])
                return replaced_data

            for k, v in data.items():
                if isinstance(v, (dict, list)):
                    data[k] = self._process_data(v, base_dir)

            return data

        return data
