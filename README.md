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

## Table of Contents

- [Features](#features)
- [Examples](#examples)
  - [Basic Usage](#basic-usage)
  - [With Caching](#with-caching)
  - [Ignoring Files](#ignoring-files)
  - [Custom Module Paths](#custom-module-paths)
- [API Reference](#api-reference)
  - [pythonFileTrace](#pythonfiletracefiles-options)
  - [parseImports](#parseimportssource-options)
  - [parseImportsRegex](#parseimportsregexsource)
  - [getPythonEnv](#getpythonenvoptions)
  - [getStdlibModules](#getstdlibmodulesoptions)
- [How It Works](#how-it-works)
  - [Import Types Handled](#import-types-handled)
- [Quirks & Edge Cases](#quirks--edge-cases)
- [License](#license)

## Features

- Traces all Python imports (standard imports, from imports, relative imports)
- Handles package imports with `__init__.py`
- Supports dynamic imports (`__import__()`, `importlib.import_module()`)
- Detects namespace packages (PEP 420)
- Provides detailed reasons for each file's inclusion
- Configurable standard library exclusion
- Caching support for multiple traces

## Examples

### Basic Usage

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

## API Reference

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

---

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

---

### `parseImportsRegex(source)`

Fallback regex-based parser (less accurate but works without Python).

```typescript
import { parseImportsRegex } from 'python-file-trace';

const imports = parseImportsRegex(source);
```

---

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

---

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

## Quirks & Edge Cases

This table documents which Python import patterns are handled and which remain unsupported.

### Handled

| Category | Pattern | Example |
|----------|---------|---------|
| **Static Imports** | | |
| Standard import | `import x` | `import os` |
| Dotted import | `import x.y.z` | `import os.path` |
| Aliased import | `import x as y` | `import numpy as np` |
| From import | `from x import y` | `from os import path` |
| From import with alias | `from x import y as z` | `from os import path as p` |
| Relative import (current) | `from . import x` | `from . import sibling` |
| Relative import (parent) | `from .. import x` | `from .. import parent` |
| Multi-level relative | `from ...pkg import x` | `from ...utils import helper` |
| Star import | `from x import *` | `from os.path import *` |
| Comma-separated | `import a, b, c` | `import os, sys, json` |
| Multi-line (parentheses) | `from x import (\n a,\n b)` | See below |
| Multi-line (backslash) | `import a, \` continuation | See below |
| Future imports | `from __future__ import x` | `from __future__ import annotations` |
| **Dynamic Imports** | | |
| Built-in | `__import__('x')` | `__import__('mymodule')` |
| importlib | `importlib.import_module('x')` | `importlib.import_module('mymodule')` |
| Aliased importlib | `il.import_module('x')` | `import importlib as il; il.import_module('mod')` |
| Direct import_module | `import_module('x')` | `from importlib import import_module; import_module('mod')` |
| Aliased import_module | `load('x')` | `from importlib import import_module as load; load('mod')` |
| With package param | `import_module('.x', 'pkg')` | `import_module('.sub', package='mypackage')` |
| Keyword arguments | `import_module(name='x')` | `import_module(name='mod', package='pkg')` |
| runpy.run_module | `runpy.run_module('x')` | `runpy.run_module('mymodule')` |
| runpy.run_path | `runpy.run_path('x.py')` | `runpy.run_path('scripts/runner.py')` |
| Aliased runpy | `rp.run_module('x')` | `import runpy as rp; rp.run_module('mod')` |
| Direct run_module | `run_module('x')` | `from runpy import run_module; run_module('mod')` |
| **Contextual Imports** | | |
| Try/except fallback | Both branches traced | `try: import fast\nexcept: import slow` |
| Conditional imports | All branches traced | `if cond: import a\nelse: import b` |
| Function-level imports | Imports inside functions | `def f(): import x` |
| Class-level imports | Imports inside classes | `class C: import x` |
| **Package Handling** | | |
| Package with `__init__.py` | Auto-includes init file | `import mypackage` |
| Submodule imports | Traces full chain | `from pkg.sub import mod` |
| Namespace packages | PEP 420 support | Packages without `__init__.py` |
| **False Positive Prevention** | | |
| String literals | Ignored | `x = "import fake"` |
| Docstrings | Ignored | `"""import fake"""` |
| Comments | Ignored | `# import fake` |

### Not Yet Handled

| Category | Pattern | Example | Reason |
|----------|---------|---------|--------|
| **Dynamic/Runtime** | | | |
| Computed module names | `__import__(f"mod_{x}")` | Dynamic string | Requires runtime analysis |
| Variable module names | `import_module(config.name)` | Variable reference | Requires runtime analysis |
| exec/eval imports | `exec("import x")` | Code execution | Security & complexity |
| **Lazy Loading** | | | |
| Module `__getattr__` | PEP 562 lazy imports | `def __getattr__(name): ...` | Requires runtime analysis |
| `__all__` expansion | What `*` actually imports | `from x import *` | Traces source, not exports |
| **System-Level** | | | |
| sys.modules manipulation | `sys.modules['x'] = mod` | Direct manipulation | Requires runtime analysis |
| Import hooks | `sys.meta_path` | Custom finders/loaders | Plugin system |
| Zipimport | Imports from .zip/.egg | Archive imports | Not implemented |
| C extensions | `.pyd`, `.so` files | Binary modules | Different file type |
| **Edge Cases** | | | |
| Circular imports | Complex cycles | `a→b→c→a` | May have edge cases |
| Non-UTF8 encodings | `# -*- coding: xxx -*-` | Rare encodings | May fail to parse |
| Syntax in dead code | Invalid syntax in `if False:` | Unexecuted branches | AST requires valid syntax |

## License

MIT
