#!/usr/bin/env python3
"""
Python AST parser for extracting import statements.
Used by python-file-trace to analyze Python files.
"""
import ast
import json
import sys
from typing import Any, Dict, Optional


def _ast_to_str(node: ast.AST) -> str:
    """
    Convert an AST node to a string representation.
    Uses ast.unparse() for Python 3.9+ or a fallback for earlier versions.
    """
    if hasattr(ast, 'unparse'):
        return ast.unparse(node)
    else:
        # Fallback for Python 3.8: handle common node types
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value_str = _ast_to_str(node.value)
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

        # Handle: __import__('module'), importlib.import_module('module')
        elif isinstance(node, ast.Call):
            dynamic = extract_dynamic_import(node)
            if dynamic:
                result["dynamicImports"].append(dynamic)

    return result


def extract_dynamic_import(node: ast.Call) -> Optional[Dict[str, Any]]:
    """Extract dynamic import information from a Call node."""
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

    # Check for importlib.import_module('module')
    if isinstance(node.func, ast.Attribute):
        if node.func.attr == "import_module":
            # Check if it's importlib.import_module or something.import_module
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "importlib":
                if node.args and isinstance(node.args[0], ast.Constant):
                    return {
                        "type": "importlib",
                        "module": node.args[0].value,
                        "line": node.lineno
                    }
                else:
                    return {
                        "type": "importlib",
                        "module": None,
                        "line": node.lineno,
                        "expression": _ast_to_str(node.args[0]) if node.args else None
                    }

    return None


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
