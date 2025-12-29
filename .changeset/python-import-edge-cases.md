---
"python-file-trace": minor
---

Add comprehensive Python import edge case handling

- Support aliased importlib (`import importlib as il; il.import_module()`)
- Support direct import_module calls (`from importlib import import_module`)
- Support import_module with package parameter for relative dynamic imports
- Support keyword arguments in import_module (`name=`, `package=`)
- Handle comma-separated imports (`import a, b, c`)
- Handle backslash line continuation in imports
- Properly ignore imports in strings, docstrings, and comments in regex fallback parser
- Handle relative dynamic imports with package parameter in tracing
