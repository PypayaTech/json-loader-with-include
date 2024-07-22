import json
import os


class JSONLoaderWithInclude:
    """A class to load data from JSON files with the ability to include data from one JSON file
        in another JSON file using special keys."""

    def __init__(self, enable_key="enabled", comment_char=None):
        self.enable_key = enable_key
        self.comment_char = comment_char

    @classmethod
    def read_json(cls, path, enable_key="enabled", comment_char=None):
        """
        Main entry point for users. Reads a JSON file and processes includes.
        """
        instance = cls(enable_key, comment_char)
        return instance._read_json(path)

    def _read_json(self, path):
        with open(path, 'r') as f:
            if self.comment_char:
                # Remove comments before parsing
                data = self._remove_comments(f.read())
                json_data = json.loads(data)
            else:
                json_data = json.load(f)
        base_dir = os.path.dirname(path)
        return self._process_data(json_data, base_dir)

    def _remove_comments(self, json_string):
        lines = json_string.split('\n')
        return '\n'.join(line.split(self.comment_char)[0].rstrip() for line in lines)

    @classmethod
    def load_from_file(cls, spec, base_dir, enable_key="enabled", comment_char=None):
        """
        Load data from a file specified in the 'spec' dictionary.
        """
        instance = cls(enable_key, comment_char)
        return instance._load_from_file(spec, base_dir)

    def _load_from_file(self, spec, base_dir):
        full_path = os.path.join(base_dir, spec["filename"])
        data = self._read_json(full_path)

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

    def _get_last_key(self, key):
        if isinstance(key, str):
            return key.split('/')[-1]
        elif isinstance(key, list):
            return key[-1]
        return key

    def _navigate_nested_key(self, data, key):
        if isinstance(key, str):
            keys = key.split('/')
        elif isinstance(key, list):
            keys = key
        else:
            return data[key]  # If it's neither string nor list, treat it as a direct key

        for k in keys:
            data = data[k]
        return data

    def _is_enabled(self, data):
        return not isinstance(data, dict) or self.enable_key not in data or data[self.enable_key]

    def _handle_enabled_flag(self, data):
        if isinstance(data, dict):
            return {k: self._handle_enabled_flag(v) for k, v in data.items() if self._is_enabled(v)}
        elif isinstance(data, list):
            return [self._handle_enabled_flag(item) for item in data if self._is_enabled(item)]
        return data

    def _process_data(self, data, base_dir):
        # Handle enabled flag before processing
        data = self._handle_enabled_flag(data)

        if isinstance(data, list):
            new_data = []
            for i, v in enumerate(data):
                if isinstance(v, dict) and "include" in v:
                    included_data = self._load_from_file(v["include"], base_dir)
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
                    included_data = self._load_from_file(data["include"], base_dir)
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
                        included_data = self._load_from_file(inc, base_dir)
                        if isinstance(included_data, dict):
                            data.update(included_data)
                        else:
                            data["included"] = included_data  # Default to 'included' key
                del data["include"]

            if "replace_value" in data:
                replace_spec = data["replace_value"]
                replaced_data = self._load_from_file(replace_spec, base_dir)
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
