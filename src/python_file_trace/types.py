"""Type definitions for python-file-trace."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class FileType(Enum):
    """Type of file inclusion."""
    INITIAL = "initial"
    IMPORT = "import"
    PACKAGE = "package"
    DATA = "data"


@dataclass
class FileReason:
    """Reason why a file was included in the trace."""
    type: FileType
    parents: set[str] = field(default_factory=set)
    ignored: bool = False
    module_name: str | None = None

    def add_parent(self, parent: str) -> None:
        """Add a parent file that caused this file to be included."""
        self.parents.add(parent)


@dataclass
class TraceResult:
    """Result of tracing Python file dependencies."""
    file_list: set[str]
    reasons: dict[str, FileReason]
    warnings: list[str]
    base: Path

    def relative_file_list(self) -> set[str]:
        """Get file list relative to base path."""
        result = set()
        for file_path in self.file_list:
            try:
                rel_path = Path(file_path).relative_to(self.base)
                result.add(str(rel_path))
            except ValueError:
                result.add(file_path)
        return result


@dataclass
class TraceOptions:
    """Options for tracing Python file dependencies."""
    base: Path | None = None
    ignore: list[str] = field(default_factory=list)
    include_stdlib: bool = False
    include_site_packages: bool = True
    follow_dynamic_imports: bool = False
    max_depth: int | None = None
