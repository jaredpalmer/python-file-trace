# python-file-trace

Determine exactly which files are necessary to run a Python application. Similar to [@vercel/nft](https://github.com/vercel/nft) (Node File Trace) but for Python.

## Quick Start

```bash
npm install python-file-trace  # requires Node.js >= 18, Python 3.8+
```

```typescript
import { pythonFileTrace } from 'python-file-trace';

const { fileList, reasons } = await pythonFileTrace(['./app.py']);

console.log([...fileList]);
// ['/project/app.py', '/project/utils.py', '/project/helpers.py']

console.log(reasons.get('/project/helpers.py'));
// { type: 'from', parents: Set { '/project/app.py' }, moduleName: 'helpers' }
```

## Features

- Traces all Python imports (standard, from, relative)
- Handles `__init__.py` and namespace packages (PEP 420)
- Supports dynamic imports (`__import__()`, `importlib.import_module()`)
- Provides reasons for each file's inclusion

## API

### `pythonFileTrace(files, options?)`

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `base` | `string` | `process.cwd()` | Base directory for resolving modules |
| `pythonPath` | `string` | `'python3'` | Python executable for AST parsing |
| `modulePaths` | `string[]` | `[]` | Additional module search paths |
| `ignore` | `string[]` | `[]` | Glob patterns to ignore |
| `includeStdlib` | `boolean` | `false` | Include standard library modules |
| `cache` | `TraceCache` | - | Cache for reusing across traces |

```typescript
interface PythonFileTraceResult {
  fileList: Set<string>;             // All files needed
  reasons: Map<string, FileReason>;  // Why each file was included
  warnings: string[];                // Warnings encountered
  unresolved: Map<string, string[]>; // Unresolved imports
}
```

## License

MIT
