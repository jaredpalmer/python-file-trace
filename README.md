# python-file-trace

Determine exactly which files are necessary to run a Python application. Similar to [@vercel/nft](https://github.com/vercel/nft) (Node File Trace) but for Python.

## Features

- Traces all Python imports (standard imports, from imports, relative imports)
- Handles package imports with `__init__.py`
- Supports dynamic imports (`__import__()`, `importlib.import_module()`)
- Detects namespace packages (PEP 420)
- Provides detailed reasons for each file's inclusion
- Configurable standard library exclusion
- Caching support for multiple traces

## Installation

```bash
npm install python-file-trace
```

## Requirements

- Node.js >= 18
- Python 3.8+ (for AST parsing, falls back to regex parser if unavailable)

## Usage

```typescript
import { pythonFileTrace } from 'python-file-trace';

const result = await pythonFileTrace(['./app.py'], {
  base: process.cwd(),
});

// result.fileList - Set of all files needed to run the application
// result.reasons - Map of file paths to inclusion reasons
// result.warnings - Array of warnings encountered
// result.unresolved - Map of unresolved imports
```

## API

### `pythonFileTrace(files, options?)`

Traces the dependencies of the given Python files.

#### Parameters

- `files: string[]` - Array of Python file paths to trace
- `options?: PythonFileTraceOptions` - Optional configuration

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `base` | `string` | `process.cwd()` | Base directory for resolving modules |
| `pythonPath` | `string` | `'python3'` | Python executable for AST parsing |
| `modulePaths` | `string[]` | `[]` | Additional module search paths |
| `followSymlinks` | `boolean` | `true` | Whether to follow symbolic links |
| `ignore` | `string[]` | `[]` | Glob patterns to ignore |
| `maxDepth` | `number` | `100` | Maximum depth for recursive tracing |
| `includeStdlib` | `boolean` | `false` | Include standard library modules |
| `analyzeDynamic` | `boolean` | `true` | Analyze dynamic imports |
| `fileIOConcurrency` | `number` | `1024` | File I/O concurrency limit |
| `cache` | `TraceCache` | - | Cache for reusing across traces |
| `readFile` | `function` | - | Custom file read function |
| `stat` | `function` | - | Custom stat function |

#### Returns

```typescript
interface PythonFileTraceResult {
  fileList: Set<string>;                    // All files needed
  reasons: Map<string, FileReason>;         // Why each file was included
  warnings: string[];                       // Warnings encountered
  unresolved: Map<string, string[]>;        // Unresolved imports
}

interface FileReason {
  type: 'input' | 'import' | 'from' | 'dynamic' | 'asset' | 'package' | 'relative' | 'namespace';
  parents: Set<string>;                     // Files that imported this file
  moduleName?: string;                      // The module name used in the import
  ignored?: boolean;                        // Whether this file matches ignore patterns
}
```

## Examples

### Basic Usage

```typescript
import { pythonFileTrace } from 'python-file-trace';

const { fileList } = await pythonFileTrace(['./main.py']);

console.log('Files needed:', [...fileList]);
```

### With Caching

```typescript
import { pythonFileTrace, type TraceCache } from 'python-file-trace';

// Create a cache for reuse
const cache: TraceCache = {
  fileContents: new Map(),
  parsedImports: new Map(),
  resolvedModules: new Map(),
  stdlibModules: new Set(),
};

// First trace
const result1 = await pythonFileTrace(['./app1.py'], { cache });

// Second trace (faster due to caching)
const result2 = await pythonFileTrace(['./app2.py'], { cache });
```

### Excluding Standard Library

```typescript
const { fileList } = await pythonFileTrace(['./main.py'], {
  includeStdlib: false,  // Default: only trace local modules
});
```

### Ignoring Files

```typescript
const { fileList } = await pythonFileTrace(['./main.py'], {
  ignore: ['**/tests/**', '**/*_test.py'],
});
```

### Custom Module Paths

```typescript
const { fileList } = await pythonFileTrace(['./main.py'], {
  modulePaths: ['/path/to/custom/modules'],
});
```

## Additional APIs

### `parseImports(source, options?)`

Parse import statements from Python source code using Python's AST.

```typescript
import { parseImports } from 'python-file-trace';

const imports = await parseImports(`
import os
from typing import Optional
from . import utils
`);

// imports.imports - Standard import statements
// imports.fromImports - From import statements
// imports.dynamicImports - Dynamic imports
```

### `parseImportsRegex(source)`

Fallback regex-based parser (less accurate but works without Python).

```typescript
import { parseImportsRegex } from 'python-file-trace';

const imports = parseImportsRegex(source);
```

### `getPythonEnv(options?)`

Get Python environment information.

```typescript
import { getPythonEnv } from 'python-file-trace';

const env = await getPythonEnv();
// env.version - Python version
// env.sysPath - sys.path directories
// env.stdlibPath - Standard library path
// env.sitePackages - Site-packages directories
```

### `getStdlibModules(options?)`

Get the set of standard library module names.

```typescript
import { getStdlibModules } from 'python-file-trace';

const stdlib = await getStdlibModules();
console.log(stdlib.has('os')); // true
```

## How It Works

1. **Input Files**: Start with the provided Python files
2. **AST Parsing**: Parse each file using Python's `ast` module to extract imports
3. **Module Resolution**: Resolve each import to a file path following Python's import system
4. **Recursive Tracing**: Trace imports from each discovered file
5. **Result Compilation**: Return the complete file list with reasons

### Import Types Handled

- `import module` - Standard module import
- `import module.submodule` - Dotted module import
- `from module import name` - From import
- `from . import name` - Relative import (current package)
- `from .. import name` - Relative import (parent package)
- `from ...module import name` - Multi-level relative import
- `__import__('module')` - Built-in dynamic import
- `importlib.import_module('module')` - importlib dynamic import

## License

MIT
