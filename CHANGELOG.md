# python-file-trace

## 0.2.0

### Minor Changes

- [#14](https://github.com/jaredpalmer/python-file-trace/pull/14) [`2c2680f`](https://github.com/jaredpalmer/python-file-trace/commit/2c2680f40757194dee86bacfd7e62b9d29c8ad83) Thanks [@jaredpalmer](https://github.com/jaredpalmer)! - Add comprehensive Python import edge case handling

  - Support aliased importlib (`import importlib as il; il.import_module()`)
  - Support direct import_module calls (`from importlib import import_module`)
  - Support import_module with package parameter for relative dynamic imports
  - Support keyword arguments in import_module (`name=`, `package=`)
  - Handle comma-separated imports (`import a, b, c`)
  - Handle backslash line continuation in imports
  - Properly ignore imports in strings, docstrings, and comments in regex fallback parser
  - Handle relative dynamic imports with package parameter in tracing

- [#17](https://github.com/jaredpalmer/python-file-trace/pull/17) [`1d8ad81`](https://github.com/jaredpalmer/python-file-trace/commit/1d8ad8113447101a9265ef62f96f810efe79b9e3) Thanks [@jaredpalmer](https://github.com/jaredpalmer)! - Add support for runpy.run_module and runpy.run_path tracing

  - Support `runpy.run_module('module')` for tracing module imports
  - Support `runpy.run_path('path.py')` for tracing file path imports
  - Support aliased runpy imports (`import runpy as rp; rp.run_module()`)
  - Support direct function imports (`from runpy import run_module`)
  - Handle keyword arguments (`mod_name=`, `path_name=`)
  - Report non-static expressions as warnings
  - Added regex fallback parser support for runpy patterns
