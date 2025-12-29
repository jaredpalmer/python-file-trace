"""Tests for the tracer module."""

from pathlib import Path

import pytest

from python_file_trace import python_file_trace, TraceOptions, FileType


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestPythonFileTrace:
    """Tests for python_file_trace function."""

    def test_trace_single_file(self):
        """Test tracing a single file with no imports."""
        utils_file = FIXTURES_DIR / "simple_project" / "utils.py"
        options = TraceOptions(
            base=FIXTURES_DIR / "simple_project",
            include_stdlib=False,
            include_site_packages=False,
        )

        result = python_file_trace([utils_file], options)

        assert str(utils_file.resolve()) in result.file_list
        assert len(result.file_list) == 1

    def test_trace_with_local_imports(self):
        """Test tracing a file that imports local modules."""
        main_file = FIXTURES_DIR / "simple_project" / "main.py"
        options = TraceOptions(
            base=FIXTURES_DIR / "simple_project",
            include_stdlib=False,
            include_site_packages=False,
        )

        result = python_file_trace([main_file], options)

        # Should include main.py, utils.py, models/__init__.py, models/user.py
        relative_files = result.relative_file_list()

        assert "main.py" in relative_files
        assert "utils.py" in relative_files
        assert Path("models/__init__.py").as_posix() in relative_files or "models/__init__.py" in relative_files

    def test_trace_with_relative_imports(self):
        """Test tracing files with relative imports."""
        init_file = FIXTURES_DIR / "relative_imports" / "package" / "__init__.py"
        options = TraceOptions(
            base=FIXTURES_DIR / "relative_imports",
            include_stdlib=False,
            include_site_packages=False,
        )

        result = python_file_trace([init_file], options)

        relative_files = result.relative_file_list()

        # Should include __init__.py, module_a.py, module_b.py
        assert any("__init__.py" in f for f in relative_files)
        assert any("module_a.py" in f for f in relative_files)
        assert any("module_b.py" in f for f in relative_files)

    def test_initial_file_type(self):
        """Test that initial files have correct type."""
        utils_file = FIXTURES_DIR / "simple_project" / "utils.py"
        options = TraceOptions(base=FIXTURES_DIR / "simple_project")

        result = python_file_trace([utils_file], options)

        reason = result.reasons[str(utils_file.resolve())]
        assert reason.type == FileType.INITIAL

    def test_import_file_type(self):
        """Test that imported files have correct type."""
        main_file = FIXTURES_DIR / "simple_project" / "main.py"
        utils_file = FIXTURES_DIR / "simple_project" / "utils.py"
        options = TraceOptions(
            base=FIXTURES_DIR / "simple_project",
            include_stdlib=False,
            include_site_packages=False,
        )

        result = python_file_trace([main_file], options)

        # utils.py should be an import type
        reason = result.reasons[str(utils_file.resolve())]
        assert reason.type == FileType.IMPORT

    def test_package_file_type(self):
        """Test that package __init__.py files have correct type."""
        main_file = FIXTURES_DIR / "simple_project" / "main.py"
        models_init = FIXTURES_DIR / "simple_project" / "models" / "__init__.py"
        options = TraceOptions(
            base=FIXTURES_DIR / "simple_project",
            include_stdlib=False,
            include_site_packages=False,
        )

        result = python_file_trace([main_file], options)

        reason = result.reasons.get(str(models_init.resolve()))
        assert reason is not None
        assert reason.type == FileType.PACKAGE

    def test_parent_tracking(self):
        """Test that parent files are tracked correctly."""
        main_file = FIXTURES_DIR / "simple_project" / "main.py"
        utils_file = FIXTURES_DIR / "simple_project" / "utils.py"
        options = TraceOptions(
            base=FIXTURES_DIR / "simple_project",
            include_stdlib=False,
            include_site_packages=False,
        )

        result = python_file_trace([main_file], options)

        reason = result.reasons[str(utils_file.resolve())]
        assert str(main_file.resolve()) in reason.parents

    def test_ignore_pattern(self):
        """Test that ignore patterns work."""
        main_file = FIXTURES_DIR / "simple_project" / "main.py"
        options = TraceOptions(
            base=FIXTURES_DIR / "simple_project",
            ignore=["**/models/**"],
            include_stdlib=False,
            include_site_packages=False,
        )

        result = python_file_trace([main_file], options)

        # models should be ignored
        relative_files = result.relative_file_list()
        models_files = [f for f in relative_files if "models" in f]
        assert len(models_files) == 0

    def test_max_depth(self):
        """Test that max_depth limits tracing depth."""
        init_file = FIXTURES_DIR / "relative_imports" / "package" / "__init__.py"
        options = TraceOptions(
            base=FIXTURES_DIR / "relative_imports",
            max_depth=0,
            include_stdlib=False,
            include_site_packages=False,
        )

        result = python_file_trace([init_file], options)

        # With max_depth=0, should only include the initial file
        assert len(result.file_list) == 1

    def test_no_circular_import_issues(self):
        """Test that circular imports don't cause infinite loops."""
        # module_a imports module_b, and __init__ imports both
        init_file = FIXTURES_DIR / "relative_imports" / "package" / "__init__.py"
        options = TraceOptions(
            base=FIXTURES_DIR / "relative_imports",
            include_stdlib=False,
            include_site_packages=False,
        )

        # Should complete without hanging
        result = python_file_trace([init_file], options)

        assert len(result.file_list) >= 1


class TestTraceOptions:
    """Tests for TraceOptions."""

    def test_default_options(self):
        """Test default option values."""
        options = TraceOptions()

        assert options.base is None
        assert options.ignore == []
        assert options.include_stdlib is False
        assert options.include_site_packages is True
        assert options.follow_dynamic_imports is False
        assert options.max_depth is None
