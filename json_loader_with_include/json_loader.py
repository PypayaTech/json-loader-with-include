import json
import os


class JSONLoaderWithInclude:
    """A class to load data from JSON files with the ability to include data from one JSON file
        in another JSON file using special keys."""

    @staticmethod
    def read_json(path):
        with open(path, 'r') as f:
            data = json.load(f)
        base_dir = os.path.dirname(path)
        return JSONLoaderWithInclude._process_data(data, base_dir)

    @staticmethod
    def load_from_file(spec, base_dir):
        full_path = os.path.join(base_dir, spec["filename"])
        data = JSONLoaderWithInclude.read_json(full_path)

        # Navigate to nested keys if keys_path is present
        if "keys_path" in spec:
            for key in spec["keys_path"]:
                data = data[key]

        if "keys" in spec:
            if isinstance(data, list):
                data = [data[i] for i in spec["keys"]]
            elif isinstance(data, dict):
                data = {k: data[k] for k in spec["keys"]}

        return data

    @staticmethod
    def _process_data(data, base_dir):
        if isinstance(data, list):
            new_data = []
            for i, v in enumerate(data):
                if isinstance(v, dict) and "include" in v:
                    included_data = JSONLoaderWithInclude.load_from_file(v["include"], base_dir)
                    if isinstance(included_data, list):
                        new_data.extend(included_data)
                    else:
                        new_data.append(included_data)
                elif isinstance(v, dict):
                    new_data.append(JSONLoaderWithInclude._process_data(v, base_dir))
                else:
                    new_data.append(data[i])
            return new_data

        elif isinstance(data, dict):
            if "include" in data:
                if isinstance(data["include"], dict):
                    included_data = JSONLoaderWithInclude.load_from_file(data["include"], base_dir)
                    if isinstance(included_data, dict):
                        data.update(included_data)
                    else:
                        # Insert included data into the main dictionary key positions
                        key_path = data["include"].get("keys_path", [])
                        if key_path:
                            last_key = key_path[-1]
                            data[last_key] = included_data
                        else:
                            data["included"] = included_data  # Default to 'included' key

                elif isinstance(data["include"], list):
                    for inc in data["include"]:
                        included_data = JSONLoaderWithInclude.load_from_file(inc, base_dir)
                        if isinstance(included_data, dict):
                            data.update(included_data)
                        else:
                            data["included"] = included_data  # Default to 'included' key
                del data["include"]

            if "replace_value" in data:
                replace_spec = data["replace_value"]
                replaced_data = JSONLoaderWithInclude.load_from_file(replace_spec, base_dir)
                if "keys" in replace_spec:
                    return {k: replaced_data[k] for k in replace_spec["keys"]}
                if "key" in replace_spec:
                    return replaced_data[replace_spec["key"]]
                return replaced_data

            for k, v in data.items():
                if isinstance(v, (dict, list)):
                    data[k] = JSONLoaderWithInclude._process_data(v, base_dir)

            return data

        return data
