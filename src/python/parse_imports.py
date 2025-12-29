#!/usr/bin/env python3
"""
Python AST parser for extracting import statements.
Used by python-file-trace to analyze Python files.
"""
import ast
import json
import sys
from typing import Any, Dict, Optional

# Maximum recursion depth for _ast_to_str fallback (Python 3.8)
# This prevents stack overflow for deeply nested attribute access like a.b.c.d...
MAX_AST_RECURSION_DEPTH = 10


def _ast_to_str(node: ast.AST, depth: int = 0) -> str:
    """
    Convert an AST node to a string representation.
    Uses ast.unparse() for Python 3.9+ or a fallback for earlier versions.
    """
    if hasattr(ast, 'unparse'):
        return ast.unparse(node)
    else:
        # Prevent excessive recursion depth
        if depth > MAX_AST_RECURSION_DEPTH:
            return "<dynamic>"
        
        # Fallback for Python 3.8: handle common node types
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value_str = _ast_to_str(node.value, depth + 1)
            return f"{value_str}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        else:
            # For other complex expressions, return a generic placeholder
            return "<dynamic>"


def parse_imports(source: str) -> Dict[str, Any]:
    """Parse a Python source file and extract all import information."""
    result: Dict[str, Any] = {
        "imports": [],
        "fromImports": [],
        "dynamicImports": [],
        "errors": []
    }

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        result["errors"].append({
            "type": "syntax",
            "message": str(e),
            "line": e.lineno or 0
        })
        return result

    # Track aliases and imports of importlib functions for dynamic import detection
    # Maps local name -> original name (e.g., {"il": "importlib", "imp_mod": "import_module"})
    importlib_aliases: Dict[str, str] = {}
    import_module_names: set = set()  # Names that refer to import_module function

    # First pass: collect importlib aliases and import_module imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                # import importlib OR import importlib as il
                if alias.name == "importlib":
                    importlib_aliases[alias.asname or "importlib"] = "importlib"
        elif isinstance(node, ast.ImportFrom):
            # from importlib import import_module OR from importlib import import_module as imp
            if node.module == "importlib" and node.level == 0:
                for alias in node.names:
                    if alias.name == "import_module":
                        import_module_names.add(alias.asname or "import_module")

    # Second pass: extract all imports
    for node in ast.walk(tree):
        # Handle: import x, import x.y, import x as y
        if isinstance(node, ast.Import):
            for alias in node.names:
                result["imports"].append({
                    "module": alias.name,
                    "alias": alias.asname,
                    "line": node.lineno
                })

        # Handle: from x import y, from . import y, from ..x import y
        elif isinstance(node, ast.ImportFrom):
            names = []
            for alias in node.names:
                names.append({
                    "name": alias.name,
                    "alias": alias.asname
                })
            result["fromImports"].append({
                "module": node.module or "",
                "names": names,
                "level": node.level,
                "line": node.lineno
            })

        # Handle: __import__('module'), importlib.import_module('module'), aliased variants
        elif isinstance(node, ast.Call):
            dynamic = extract_dynamic_import(node, importlib_aliases, import_module_names)
            if dynamic:
                result["dynamicImports"].append(dynamic)

    return result


def extract_dynamic_import(
    node: ast.Call,
    importlib_aliases: Optional[Dict[str, str]] = None,
    import_module_names: Optional[set] = None
) -> Optional[Dict[str, Any]]:
    """Extract dynamic import information from a Call node.

    Args:
        node: The AST Call node to analyze
        importlib_aliases: Dict mapping local names to "importlib" (for aliased imports)
        import_module_names: Set of names that refer to import_module function
    """
    if importlib_aliases is None:
        importlib_aliases = {"importlib": "importlib"}
    if import_module_names is None:
        import_module_names = set()

    # Check for __import__('module')
    if isinstance(node.func, ast.Name) and node.func.id == "__import__":
        if node.args and isinstance(node.args[0], ast.Constant):
            return {
                "type": "builtin",
                "module": node.args[0].value,
                "line": node.lineno
            }
        else:
            return {
                "type": "builtin",
                "module": None,
                "line": node.lineno,
                "expression": _ast_to_str(node.args[0]) if node.args else None
            }

    # Check for direct import_module('module') call (from importlib import import_module)
    if isinstance(node.func, ast.Name) and node.func.id in import_module_names:
        return _extract_import_module_call(node)

    # Check for importlib.import_module('module') or aliased variants (il.import_module)
    if isinstance(node.func, ast.Attribute):
        if node.func.attr == "import_module":
            if isinstance(node.func.value, ast.Name):
                # Check if it's importlib.import_module or an aliased variant
                # Also allow "importlib" even if not explicitly imported (for backwards compatibility)
                if node.func.value.id in importlib_aliases or node.func.value.id == "importlib":
                    return _extract_import_module_call(node)

    return None


def _extract_import_module_call(node: ast.Call) -> Dict[str, Any]:
    """Extract import information from an import_module() call.

    Handles both positional and keyword arguments:
    - import_module('module')
    - import_module('.submodule', 'package')
    - import_module('.submodule', package='package')
    - import_module(name='.submodule', package='package')
    """
    module_name = None
    package_name = None
    expression = None

    # Extract first positional arg (module name)
    if node.args:
        first_arg = node.args[0]
        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
            module_name = first_arg.value
        else:
            expression = _ast_to_str(first_arg)

    # Check for 'name' keyword argument
    for kw in node.keywords:
        if kw.arg == "name" and isinstance(kw.value, ast.Constant):
            module_name = kw.value.value
            break

    # Extract package parameter (2nd positional or keyword)
    if len(node.args) >= 2:
        second_arg = node.args[1]
        if isinstance(second_arg, ast.Constant) and isinstance(second_arg.value, str):
            package_name = second_arg.value

    # Check for 'package' keyword argument
    for kw in node.keywords:
        if kw.arg == "package" and isinstance(kw.value, ast.Constant):
            package_name = kw.value.value
            break

    result: Dict[str, Any] = {
        "type": "importlib",
        "line": node.lineno
    }

    if module_name is not None:
        # Handle relative imports with package parameter
        if module_name.startswith('.') and package_name:
            # Count leading dots for level
            level = 0
            for char in module_name:
                if char == '.':
                    level += 1
                else:
                    break
            result["module"] = module_name
            result["package"] = package_name
            result["level"] = level
        else:
            result["module"] = module_name
    else:
        result["module"] = None
        result["expression"] = expression

    return result


def get_python_env() -> Dict[str, Any]:
    """Get Python environment information."""
    import sysconfig
    import site

    stdlib_path = sysconfig.get_path("stdlib")

    return {
        "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "sysPath": sys.path,
        "stdlibPath": stdlib_path or "",
        "sitePackages": site.getsitepackages() if hasattr(site, 'getsitepackages') else []
    }


def main():
    """Main entry point for the parser."""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command specified"}))
        sys.exit(1)

    command = sys.argv[1]

    if command == "parse":
        # Read source from stdin
        source = sys.stdin.read()
        result = parse_imports(source)
        print(json.dumps(result))

    elif command == "env":
        result = get_python_env()
        print(json.dumps(result))

    elif command == "stdlib":
        # List standard library modules
        import pkgutil
        import sysconfig

        stdlib_path = sysconfig.get_path("stdlib")
        stdlib_modules = set()

        if stdlib_path:
            for importer, modname, ispkg in pkgutil.iter_modules([stdlib_path]):
                stdlib_modules.add(modname)

        # Add built-in modules
        stdlib_modules.update(sys.builtin_module_names)

        print(json.dumps(sorted(stdlib_modules)))

    else:
        print(json.dumps({"error": f"Unknown command: {command}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
