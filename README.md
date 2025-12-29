# python-file-trace

Determine exactly which files are necessary to run a Python application. Similar to [@vercel/nft](https://github.com/vercel/nft) (Node File Trace) but for Python.

## Quick Start

```bash
npm install python-file-trace
```

> **Requires:** Node.js 18+ and Python 3.8+ (falls back to regex parsing if Python unavailable)

Given a Python application with imports:

```python
# app.py
import utils
from helpers import helper_func

def main():
    utils.do_something()
    helper_func()
```

Trace all files needed to run it:

```typescript
import { pythonFileTrace } from 'python-file-trace';

const { fileList, reasons } = await pythonFileTrace(['./app.py']);

console.log([...fileList]);
// [
//   '/project/app.py',
//   '/project/utils.py',
//   '/project/helpers.py'
// ]

// See why each file was included
console.log(reasons.get('/project/helpers.py'));
// { type: 'from', parents: Set { '/project/app.py' }, moduleName: 'helpers' }
```

## Features

- Traces all Python imports (standard imports, from imports, relative imports)
- Handles package imports with `__init__.py`
- Supports dynamic imports (`__import__()`, `importlib.import_module()`)
- Detects namespace packages (PEP 420)
- Provides detailed reasons for each file's inclusion
- Configurable standard library exclusion
- Caching support for multiple traces

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

// Second trace reuses cached data
const result2 = await pythonFileTrace(['./app2.py'], { cache });
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

| Import Pattern | Example | Supported |
|----------------|---------|-----------|
| Standard import | `import os` | ✅ |
| Dotted import | `import os.path` | ✅ |
| Aliased import | `import numpy as np` | ✅ |
| Comma-separated | `import os, sys, json` | ✅ |
| From import | `from os import path` | ✅ |
| From import multiple | `from os import path, getcwd` | ✅ |
| From import aliased | `from os import path as p` | ✅ |
| Star import | `from os.path import *` | ✅ |
| Relative import (current) | `from . import sibling` | ✅ |
| Relative import (parent) | `from .. import parent` | ✅ |
| Relative import (deep) | `from ...pkg import module` | ✅ |
| Package import | `import mypackage` (with `__init__.py`) | ✅ |
| Namespace package | `import mypkg` (PEP 420, no `__init__.py`) | ✅ |

### Dynamic Import Patterns

| Pattern | Example | Supported |
|---------|---------|-----------|
| Built-in `__import__` | `__import__('module')` | ✅ |
| importlib standard | `importlib.import_module('module')` | ✅ |
| importlib aliased | `import importlib as il; il.import_module('mod')` | ✅ |
| Direct import_module | `from importlib import import_module; import_module('mod')` | ✅ |
| Aliased import_module | `from importlib import import_module as load; load('mod')` | ✅ |
| With package param | `import_module('.sub', package='pkg')` | ✅ |
| With keyword args | `import_module(name='mod', package='pkg')` | ✅ |
| Non-static expression | `import_module(get_name())` | ⚠️ Warning |

### Edge Cases Handled

| Edge Case | Description | Status |
|-----------|-------------|--------|
| Try/except fallbacks | `try: import fast except: import slow` | ✅ Both branches traced |
| Conditional imports | `if WINDOWS: import win else: import unix` | ✅ All branches traced |
| Function-scoped imports | `def f(): import module` | ✅ Traced |
| Multi-line with backslash | `import a, \`<br>`    b, c` | ✅ Handled |
| Multi-line with parens | `from x import (`<br>`    a, b)` | ✅ Handled |
| Imports in strings | `x = "import fake"` | ✅ Ignored (not traced) |
| Imports in docstrings | `"""import fake"""` | ✅ Ignored (not traced) |
| Imports in comments | `# import fake` | ✅ Ignored (not traced) |
| `__future__` imports | `from __future__ import annotations` | ✅ Parsed |
| Circular imports | A imports B, B imports A | ✅ Handled |
| Missing modules | Import of non-existent module | ✅ Added to `unresolved` |
| Syntax errors | Invalid Python syntax | ✅ Partial parsing with warning |

### Limitations

| Limitation | Description |
|------------|-------------|
| Runtime-generated names | `import_module(f"plugin_{name}")` cannot be statically analyzed |
| `exec`/`eval` imports | `exec("import module")` not detected |
| Plugin loaders | Custom import machinery not supported |
| Lazy `__getattr__` | Module-level lazy loading via `__getattr__` not traced |
| Zip imports | Imports from `.zip` files not supported |
| C extensions | `.so`/`.pyd` files detected but not analyzed |

## License

MIT
