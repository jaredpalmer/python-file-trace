"""
Python File Trace - Determine which files are needed to run a Python application.

This package provides functionality similar to @vercel/nft for Node.js,
but for Python applications. It analyzes import statements to determine
the complete set of files required to run an application.

Example:
    >>> from python_file_trace import python_file_trace, TraceOptions
    >>> result = python_file_trace(["./main.py"])
    >>> print(result.relative_file_list())
    {'main.py', 'utils.py', 'models/__init__.py'}
"""

from .tracer import Tracer, python_file_trace
from .types import FileReason, FileType, TraceOptions, TraceResult

__all__ = [
    "python_file_trace",
    "Tracer",
    "TraceOptions",
    "TraceResult",
    "FileReason",
    "FileType",
]

__version__ = "0.1.0"
