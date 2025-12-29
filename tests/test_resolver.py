"""Tests for the resolver module."""

from pathlib import Path

import pytest

from python_file_trace.analyzer import ImportInfo
from python_file_trace.resolver import (
    resolve_absolute_import,
    resolve_import,
    resolve_relative_import,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestResolveAbsoluteImport:
    """Tests for resolve_absolute_import function."""

    def test_resolve_module(self):
        """Test resolving a simple module."""
        search_paths = [FIXTURES_DIR / "simple_project"]
        result = resolve_absolute_import("utils", search_paths)

        assert result is not None
        assert result.name == "utils.py"

    def test_resolve_package(self):
        """Test resolving a package."""
        search_paths = [FIXTURES_DIR / "simple_project"]
        result = resolve_absolute_import("models", search_paths)

        assert result is not None
        assert result.name == "__init__.py"
        assert result.parent.name == "models"

    def test_resolve_submodule(self):
        """Test resolving a submodule."""
        search_paths = [FIXTURES_DIR / "simple_project"]
        result = resolve_absolute_import("models.user", search_paths)

        assert result is not None
        assert result.name == "user.py"

    def test_not_found_returns_none(self):
        """Test that non-existent module returns None."""
        search_paths = [FIXTURES_DIR / "simple_project"]
        result = resolve_absolute_import("nonexistent", search_paths)

        assert result is None


class TestResolveRelativeImport:
    """Tests for resolve_relative_import function."""

    def test_single_dot_import(self):
        """Test resolving single dot relative import."""
        from_file = FIXTURES_DIR / "relative_imports" / "package" / "module_a.py"
        import_info = ImportInfo(
            module="module_b",
            names=["func_b"],
            is_from_import=True,
            level=1,
            lineno=1,
        )

        result = resolve_relative_import(import_info, from_file)

        assert result is not None
        assert result.name == "module_b.py"

    def test_double_dot_import(self):
        """Test resolving double dot relative import."""
        from_file = FIXTURES_DIR / "relative_imports" / "package" / "module_a.py"
        import_info = ImportInfo(
            module="",
            names=["something"],
            is_from_import=True,
            level=2,
            lineno=1,
        )

        # Should go up two levels from package/module_a.py
        result = resolve_relative_import(import_info, from_file)
        # Will be the relative_imports directory itself (no __init__.py)


class TestResolveImport:
    """Tests for resolve_import function."""

    def test_resolves_absolute(self):
        """Test that absolute imports are resolved."""
        from_file = FIXTURES_DIR / "simple_project" / "main.py"
        import_info = ImportInfo(
            module="utils",
            names=[],
            is_from_import=False,
            level=0,
            lineno=1,
        )
        search_paths = [FIXTURES_DIR / "simple_project"]

        result = resolve_import(import_info, from_file, search_paths)

        assert result is not None
        assert result.name == "utils.py"

    def test_resolves_relative(self):
        """Test that relative imports are resolved."""
        from_file = FIXTURES_DIR / "relative_imports" / "package" / "module_a.py"
        import_info = ImportInfo(
            module="module_b",
            names=["func_b"],
            is_from_import=True,
            level=1,
            lineno=1,
        )

        result = resolve_import(import_info, from_file, [])

        assert result is not None
        assert result.name == "module_b.py"
