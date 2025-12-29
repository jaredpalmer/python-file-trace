"""AST analysis for extracting imports from Python files."""

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ImportInfo:
    """Information about an import statement."""
    module: str
    names: list[str]
    is_from_import: bool
    level: int  # 0 for absolute, > 0 for relative
    lineno: int


def analyze_file(file_path: Path) -> list[ImportInfo]:
    """
    Analyze a Python file and extract all import statements.

    Args:
        file_path: Path to the Python file to analyze.

    Returns:
        List of ImportInfo objects describing each import.
    """
    try:
        source = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    return analyze_source(source)


def analyze_source(source: str) -> list[ImportInfo]:
    """
    Analyze Python source code and extract all import statements.

    Args:
        source: Python source code string.

    Returns:
        List of ImportInfo objects describing each import.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    imports: list[ImportInfo] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(ImportInfo(
                    module=alias.name,
                    names=[],
                    is_from_import=False,
                    level=0,
                    lineno=node.lineno,
                ))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = [alias.name for alias in node.names]
            imports.append(ImportInfo(
                module=module,
                names=names,
                is_from_import=True,
                level=node.level,
                lineno=node.lineno,
            ))

    return imports


def extract_dynamic_imports(source: str) -> list[str]:
    """
    Extract potential dynamic imports from __import__() and importlib calls.

    This performs best-effort extraction of string literals passed to
    dynamic import functions.

    Args:
        source: Python source code string.

    Returns:
        List of module names that may be dynamically imported.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    dynamic_imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check for __import__("module")
            if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                if node.args and isinstance(node.args[0], ast.Constant):
                    if isinstance(node.args[0].value, str):
                        dynamic_imports.append(node.args[0].value)

            # Check for importlib.import_module("module")
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == "import_module":
                    if node.args and isinstance(node.args[0], ast.Constant):
                        if isinstance(node.args[0].value, str):
                            dynamic_imports.append(node.args[0].value)

    return dynamic_imports
