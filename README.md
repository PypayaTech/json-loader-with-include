# pypaya-json

Enhanced JSON processing with includes, comments, path resolution, and more.

## Features

- **File Inclusions**: Include other JSON files using `"include"` declarations
- **Comment Support**: Add comments to JSON files using custom comment characters
- **Path Resolution**: Automatically resolve relative paths to absolute paths using `@path:` annotations
- **Flexible Configuration**: Use as class methods for one-time operations or instances for reusable configurations
- **Nested Key Access**: Navigate and extract data from nested JSON structures
- **Conditional Processing**: Enable/disable sections using custom enable keys
- **Value Replacement**: Replace entire sections with data from external files

## Installation

```bash
pip install pypaya-json
```

## Quick start

### One-time usage (class method)

```python
from pypaya_json import PypayaJSON

# Basic loading
data = PypayaJSON.load("config.json")

# With comments support and path resolution
data = PypayaJSON.load("config.json", comment_string="#")

# With custom enable key and path annotations disabled
data = PypayaJSON.load("config.json", enable_key="active", resolve_path_annotations=False)

# With custom path annotation prefix
data = PypayaJSON.load("config.json", path_annotation_prefix="$resolve:")
```

### Reusable configuration (instance)

```python
from pypaya_json import PypayaJSON

# Create a reusable loader
loader = PypayaJSON(enable_key="active", comment_string="//")

# Load multiple files with same settings
config = loader.load_file("config.json")
settings = loader.load_file("settings.json")
```

## Examples

### Path resolution

**config.json**:
```json
{
  "training": {
    "@path:data_dir": "../../data/training",
    "@path:checkpoint": "../models/best.ckpt"
  },
  "output": {
    "@path:save_dir": "./outputs"
  }
}
```

**Result**:
```python
data = PypayaJSON.load("config.json")
# {
#   "training": {
#     "data_dir": "/absolute/path/to/data/training",
#     "checkpoint": "/absolute/path/to/models/best.ckpt"
#   },
#   "output": {
#     "save_dir": "/absolute/path/to/project/outputs"
#   }
# }
```

### Basic file inclusion

**main.json**:
```json
{
  "app_name": "MyApp",
  "include": {
    "filename": "database.json"
  },
  "features": ["auth", "api"]
}
```

**database.json**:
```json
{
  "host": "localhost",
  "port": 5432,
  "name": "myapp_db"
}
```

**Result**:
```python
data = PypayaJSON.load("main.json")
# {
#   "app_name": "MyApp",
#   "host": "localhost",
#   "port": 5432,
#   "name": "myapp_db",
#   "features": ["auth", "api"]
# }
```

### Comments support

**config.json**:
```json
{
  "server": {
    "host": "0.0.0.0",    // Bind to all interfaces
    "port": 8080          // Default port
  },
  // "debug": true,       // Commented out
  "workers": 4
}
```

```python
data = PypayaJSON.load("config.json", comment_string="//")
# Comments are automatically stripped
```

### Combined path resolution and includes

**main.json**:
```json
{
  "@path:base_dir": "../data",
  "include": {
    "filename": "models.json"
  }
}
```

**models.json**:
```json
{
  "@path:checkpoint_dir": "./checkpoints",
  "model_name": "best_model.ckpt"
}
```

**Result**: All paths resolved relative to their respective config file locations

### Nested key access

**data.json**:
```json
{
  "database": {
    "connections": {
      "primary": "postgresql://...",
      "replica": "postgresql://..."
    }
  }
}
```

**main.json**:
```json
{
  "include": {
    "filename": "data.json",
    "keys_path": "database/connections/primary"
  }
}
```

**Result**: `"postgresql://..."`

### Conditional inclusion

```json
{
  "base_config": "value",
  "include": {
    "filename": "optional.json",
    "enabled": false
  }
}
```

```python
# With custom enable key
loader = PypayaJSON(enable_key="active")
data = loader.load_file("config.json")
```

### Value replacement

```json
{
  "database": {
    "replace_value": {
      "filename": "secrets.json",
      "key": "database_url"
    }
  }
}
```

### Custom path annotation prefix

```json
{
  "$resolve:data_dir": "../../data",
  "$resolve:model_path": "../models/best.ckpt"
}
```

```python
data = PypayaJSON.load("config.json", path_annotation_prefix="$resolve:")
```

## API Reference

### PypayaJSON class

#### Class methods

- `PypayaJSON.load(path, enable_key="enabled", comment_string=None, resolve_path_annotations=True, path_annotation_prefix="@path:")` - Load JSON file with one-time configuration

#### Instance methods

- `PypayaJSON(enable_key="enabled", comment_string=None, resolve_path_annotations=True, path_annotation_prefix="@path:")` - Create reusable loader instance
- `loader.load_file(path)` - Load JSON file using instance configuration

#### Parameters

- `path` (str): Path to the JSON file
- `enable_key` (str): Key used for conditional inclusion (default: "enabled")
- `comment_string` (str, optional): String that denotes comments (default: None)
- `resolve_path_annotations` (bool): Whether to resolve path annotations (default: True)
- `path_annotation_prefix` (str): Prefix for path annotation keys (default: "@path:")

## Advanced usage

### Multiple inclusions

```json
{
  "include": [
    {"filename": "config1.json"},
    {"filename": "config2.json", "keys": ["specific_key"]},
    {"filename": "config3.json", "enabled": false}
  ]
}
```

### Specific key selection

```json
{
  "include": {
    "filename": "large_config.json",
    "keys": ["database", "cache", "logging"]
  }
}
```

### Deep nested access

```json
{
  "include": {
    "filename": "nested.json",
    "keys_path": ["level1", "level2", "target_key"]
  }
}
```

### Complex configuration with all features

```json
{
  // Application settings
  "app": {
    "@path:base_dir": "../../app",
    "name": "MyApp"
  },
  
  // Include database config
  "include": {
    "filename": "database.json",
    "keys": ["production"]
  },
  
  // Model configuration with paths
  "model": {
    "@path:checkpoint_dir": "./checkpoints",
    "@path:data_dir": "../data",
    "config": {
      "replace_value": {
        "filename": "model_params.json",
        "key": "transformer"
      }
    }
  },
  
  // Optional development settings
  "dev_tools": {
    "enabled": false,
    "@path:debug_dir": "./debug"
  }
}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.
