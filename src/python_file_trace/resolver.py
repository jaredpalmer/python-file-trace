"""Module resolution for Python imports."""

import sys
import sysconfig
from pathlib import Path

from .analyzer import ImportInfo


def get_stdlib_paths() -> set[Path]:
    """Get paths to the Python standard library."""
    paths = set()

    # Standard library location
    stdlib = sysconfig.get_path("stdlib")
    if stdlib:
        paths.add(Path(stdlib).resolve())

    # Platform-specific stdlib
    platstdlib = sysconfig.get_path("platstdlib")
    if platstdlib:
        paths.add(Path(platstdlib).resolve())

    return paths


def get_site_packages_paths() -> set[Path]:
    """Get paths to site-packages directories."""
    paths = set()

    purelib = sysconfig.get_path("purelib")
    if purelib:
        paths.add(Path(purelib).resolve())

    platlib = sysconfig.get_path("platlib")
    if platlib:
        paths.add(Path(platlib).resolve())

    return paths


def is_stdlib_path(path: Path, stdlib_paths: set[Path] | None = None) -> bool:
    """Check if a path is within the standard library."""
    if stdlib_paths is None:
        stdlib_paths = get_stdlib_paths()

    resolved = path.resolve()
    for stdlib_path in stdlib_paths:
        try:
            resolved.relative_to(stdlib_path)
            return True
        except ValueError:
            continue
    return False


def is_site_packages_path(path: Path, site_paths: set[Path] | None = None) -> bool:
    """Check if a path is within site-packages."""
    if site_paths is None:
        site_paths = get_site_packages_paths()

    resolved = path.resolve()
    for site_path in site_paths:
        try:
            resolved.relative_to(site_path)
            return True
        except ValueError:
            continue
    return False


def resolve_relative_import(
    import_info: ImportInfo,
    from_file: Path,
) -> Path | None:
    """
    Resolve a relative import to a file path.

    Args:
        import_info: The import information with level > 0.
        from_file: The file containing the import statement.

    Returns:
        Resolved path or None if not found.
    """
    # Start from the directory containing the importing file
    current = from_file.parent

    # Go up directories based on the level
    for _ in range(import_info.level - 1):
        current = current.parent

    # If there's a module name, resolve it
    if import_info.module:
        parts = import_info.module.split(".")
        for part in parts:
            current = current / part

    return _find_module_file(current)


def resolve_absolute_import(
    module_name: str,
    search_paths: list[Path] | None = None,
) -> Path | None:
    """
    Resolve an absolute import to a file path.

    Args:
        module_name: The fully qualified module name.
        search_paths: Paths to search for the module.

    Returns:
        Resolved path or None if not found.
    """
    if search_paths is None:
        search_paths = [Path(p) for p in sys.path if p]

    parts = module_name.split(".")

    for base_path in search_paths:
        if not base_path.exists():
            continue

        current = base_path
        for part in parts:
            current = current / part

        result = _find_module_file(current)
        if result:
            return result

    return None


def _find_module_file(path: Path) -> Path | None:
    """
    Find the actual file for a module path.

    Checks for:
    1. path.py (regular module)
    2. path/__init__.py (package)

    Args:
        path: The base path to check.

    Returns:
        Path to the module file or None.
    """
    # Check for regular module
    py_file = path.with_suffix(".py")
    if py_file.is_file():
        return py_file.resolve()

    # Check for package
    init_file = path / "__init__.py"
    if init_file.is_file():
        return init_file.resolve()

    # Check for namespace package (directory without __init__.py)
    if path.is_dir():
        # Return the directory itself for namespace packages
        return path.resolve()

    return None


def resolve_import(
    import_info: ImportInfo,
    from_file: Path,
    search_paths: list[Path] | None = None,
) -> Path | None:
    """
    Resolve an import to a file path.

    Args:
        import_info: The import information.
        from_file: The file containing the import statement.
        search_paths: Paths to search for absolute imports.

    Returns:
        Resolved path or None if not found.
    """
    if import_info.level > 0:
        return resolve_relative_import(import_info, from_file)
    else:
        return resolve_absolute_import(import_info.module, search_paths)


def get_package_files(package_path: Path) -> list[Path]:
    """
    Get all Python files in a package directory.

    Args:
        package_path: Path to the package directory.

    Returns:
        List of Python file paths in the package.
    """
    if not package_path.is_dir():
        return []

    files = []
    for py_file in package_path.rglob("*.py"):
        files.append(py_file.resolve())

    return files
