# python-file-trace

Determine which files are needed to run a Python application by tracing imports.

Similar to [@vercel/nft](https://github.com/vercel/nft) for Node.js, this package analyzes Python import statements to determine the complete set of files required to run an application. Unlike bundlers, it performs no bundling - just file tracing.

## Features

- Traces `import` and `from ... import` statements
- Supports relative imports (`.`, `..`, etc.)
- Handles packages (`__init__.py`) and submodules
- Detects dynamic imports (`__import__()`, `importlib.import_module()`)
- Provides detailed reasons for why each file was included
- Configurable filtering (ignore patterns, stdlib, site-packages)
- CLI and programmatic API

## Installation

```bash
pip install python-file-trace
```

Or with uv:

```bash
uv add python-file-trace
```

## Quick Start

### CLI Usage

```bash
# Basic usage - trace dependencies of main.py
python-file-trace main.py

# Output relative paths
python-file-trace main.py --base . --relative

# Show why each file was included
python-file-trace main.py --show-reasons

# JSON output
python-file-trace main.py --json

# Exclude site-packages
python-file-trace main.py --no-site-packages

# Ignore specific patterns
python-file-trace main.py --ignore "**/tests/**" --ignore "**/__pycache__/**"
```

### Programmatic API

```python
from python_file_trace import python_file_trace, TraceOptions

# Basic usage
result = python_file_trace(["./main.py"])
print(result.file_list)
# {'/path/to/main.py', '/path/to/utils.py', '/path/to/models/__init__.py', ...}

# With options
options = TraceOptions(
    base=Path("./src"),
    ignore=["**/tests/**"],
    include_stdlib=False,
    include_site_packages=False,
)
result = python_file_trace(["./src/main.py"], options)

# Get relative paths
print(result.relative_file_list())
# {'main.py', 'utils.py', 'models/__init__.py'}

# Check why a file was included
for file_path, reason in result.reasons.items():
    print(f"{file_path}: {reason.type.value} from {reason.parents}")
```

## API Reference

### `python_file_trace(files, options=None)`

Trace Python file dependencies.

**Parameters:**
- `files`: List of entry point files to trace
- `options`: Optional `TraceOptions` object

**Returns:** `TraceResult` object

### `TraceOptions`

Configuration options for tracing.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `base` | `Path` | `cwd()` | Base directory for relative path output |
| `ignore` | `list[str]` | `[]` | Glob patterns to ignore |
| `include_stdlib` | `bool` | `False` | Include standard library files |
| `include_site_packages` | `bool` | `True` | Include site-packages files |
| `follow_dynamic_imports` | `bool` | `False` | Attempt to trace dynamic imports |
| `max_depth` | `int \| None` | `None` | Maximum import depth to trace |

### `TraceResult`

Result of tracing.

| Property | Type | Description |
|----------|------|-------------|
| `file_list` | `set[str]` | Set of absolute file paths |
| `reasons` | `dict[str, FileReason]` | Why each file was included |
| `warnings` | `list[str]` | Warnings encountered during tracing |
| `base` | `Path` | Base directory used |

**Methods:**
- `relative_file_list()`: Get file paths relative to base

### `FileReason`

Information about why a file was included.

| Property | Type | Description |
|----------|------|-------------|
| `type` | `FileType` | How the file was included |
| `parents` | `set[str]` | Files that imported this one |
| `ignored` | `bool` | Whether the file was ignored |
| `module_name` | `str \| None` | The import module name |

### `FileType`

Enum for file inclusion types:
- `INITIAL`: Entry point file
- `IMPORT`: Imported module
- `PACKAGE`: Package `__init__.py`
- `DATA`: Data file (future)

## CLI Options

```
usage: python-file-trace [-h] [--base BASE] [--ignore IGNORE]
                         [--include-stdlib] [--no-site-packages]
                         [--follow-dynamic] [--max-depth MAX_DEPTH]
                         [--json] [--relative] [--show-reasons]
                         [--version]
                         files [files ...]

Trace Python file dependencies.

positional arguments:
  files                Entry point file(s) to trace

options:
  -h, --help           show this help message and exit
  --base BASE          Base directory for resolving relative paths
  --ignore IGNORE      Glob pattern(s) to ignore (can be repeated)
  --include-stdlib     Include standard library files in output
  --no-site-packages   Exclude site-packages from output
  --follow-dynamic     Attempt to follow dynamic imports
  --max-depth N        Maximum depth to trace
  --json               Output results as JSON
  --relative           Output paths relative to base directory
  --show-reasons       Show why each file was included
  --version            show program's version number and exit
```

## Use Cases

- **Serverless deployments**: Identify minimal files needed for Lambda/Cloud Functions
- **Container optimization**: Build smaller Docker images with only necessary files
- **Dependency analysis**: Understand your project's import graph
- **Build tools**: Create optimized production builds

## Limitations

- Only traces static imports by default (use `--follow-dynamic` for best-effort dynamic import tracing)
- Does not execute code - purely static analysis
- May not resolve all edge cases (conditional imports, string manipulation)
- Namespace packages are partially supported

## License

MIT
