"""Tests for the analyzer module."""

import pytest

from python_file_trace.analyzer import (
    ImportInfo,
    analyze_source,
    extract_dynamic_imports,
)


class TestAnalyzeSource:
    """Tests for analyze_source function."""

    def test_simple_import(self):
        """Test parsing a simple import statement."""
        source = "import os"
        imports = analyze_source(source)

        assert len(imports) == 1
        assert imports[0].module == "os"
        assert imports[0].is_from_import is False
        assert imports[0].level == 0

    def test_multiple_imports(self):
        """Test parsing multiple import statements."""
        source = """
import os
import sys
import json
"""
        imports = analyze_source(source)

        assert len(imports) == 3
        modules = {imp.module for imp in imports}
        assert modules == {"os", "sys", "json"}

    def test_from_import(self):
        """Test parsing from...import statement."""
        source = "from os.path import join, exists"
        imports = analyze_source(source)

        assert len(imports) == 1
        assert imports[0].module == "os.path"
        assert imports[0].is_from_import is True
        assert imports[0].level == 0
        assert set(imports[0].names) == {"join", "exists"}

    def test_relative_import(self):
        """Test parsing relative import statements."""
        source = "from . import module"
        imports = analyze_source(source)

        assert len(imports) == 1
        assert imports[0].module == ""
        assert imports[0].level == 1

    def test_relative_import_with_module(self):
        """Test parsing relative import with module name."""
        source = "from ..utils import helper"
        imports = analyze_source(source)

        assert len(imports) == 1
        assert imports[0].module == "utils"
        assert imports[0].level == 2
        assert imports[0].names == ["helper"]

    def test_dotted_import(self):
        """Test parsing dotted import."""
        source = "import os.path"
        imports = analyze_source(source)

        assert len(imports) == 1
        assert imports[0].module == "os.path"

    def test_aliased_import(self):
        """Test parsing aliased import."""
        source = "import numpy as np"
        imports = analyze_source(source)

        assert len(imports) == 1
        assert imports[0].module == "numpy"

    def test_star_import(self):
        """Test parsing star import."""
        source = "from os import *"
        imports = analyze_source(source)

        assert len(imports) == 1
        assert "*" in imports[0].names

    def test_syntax_error_returns_empty(self):
        """Test that syntax errors return empty list."""
        source = "import def"
        imports = analyze_source(source)

        assert imports == []

    def test_mixed_imports(self):
        """Test parsing mixed import types."""
        source = """
import os
from pathlib import Path
from . import local
from ..utils import helper
"""
        imports = analyze_source(source)

        assert len(imports) == 4


class TestExtractDynamicImports:
    """Tests for extract_dynamic_imports function."""

    def test_dunder_import(self):
        """Test extracting __import__ calls."""
        source = '__import__("os")'
        dynamic = extract_dynamic_imports(source)

        assert "os" in dynamic

    def test_importlib_import_module(self):
        """Test extracting importlib.import_module calls."""
        source = 'importlib.import_module("json")'
        dynamic = extract_dynamic_imports(source)

        assert "json" in dynamic

    def test_variable_import_not_extracted(self):
        """Test that variable imports are not extracted."""
        source = """
module_name = "os"
__import__(module_name)
"""
        dynamic = extract_dynamic_imports(source)

        assert "os" not in dynamic

    def test_multiple_dynamic_imports(self):
        """Test extracting multiple dynamic imports."""
        source = """
__import__("os")
importlib.import_module("sys")
__import__("json")
"""
        dynamic = extract_dynamic_imports(source)

        assert set(dynamic) == {"os", "sys", "json"}
