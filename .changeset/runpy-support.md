---
"python-file-trace": minor
---

Add support for runpy.run_module and runpy.run_path tracing

- Support `runpy.run_module('module')` for tracing module imports
- Support `runpy.run_path('path.py')` for tracing file path imports
- Support aliased runpy imports (`import runpy as rp; rp.run_module()`)
- Support direct function imports (`from runpy import run_module`)
- Handle keyword arguments (`mod_name=`, `path_name=`)
- Report non-static expressions as warnings
- Added regex fallback parser support for runpy patterns
