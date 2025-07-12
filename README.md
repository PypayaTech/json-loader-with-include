# pypaya-json

Enhanced JSON processing with includes, comments, and more.

## Features

- **File Inclusions**: Include other JSON files using `"include"` declarations
- **Comment Support**: Add comments to JSON files using custom comment characters
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

# With comments support
data = PypayaJSON.load("config.json", comment_string="#")

# With custom enable key
data = PypayaJSON.load("config.json", enable_key="active")
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

## API Reference

### PypayaJSON class

#### Class methods

- `PypayaJSON.load(path, enable_key="enabled", comment_char=None)` - Load JSON file with one-time configuration

#### Instance methods

- `PypayaJSON(enable_key="enabled", comment_char=None)` - Create reusable loader instance
- `loader.load_file(path)` - Load JSON file using instance configuration

#### Parameters

- `path` (str): Path to the JSON file
- `enable_key` (str): Key used for conditional inclusion (default: "enabled")
- `comment_char` (str, optional): Character that denotes comments (default: None)

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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.
