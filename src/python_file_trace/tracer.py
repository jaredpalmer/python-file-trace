"""Main tracing logic for Python file dependencies."""

import fnmatch
import sys
from pathlib import Path

from .analyzer import ImportInfo, analyze_file, extract_dynamic_imports
from .resolver import (
    get_site_packages_paths,
    get_stdlib_paths,
    is_site_packages_path,
    is_stdlib_path,
    resolve_import,
)
from .types import FileReason, FileType, TraceOptions, TraceResult


class Tracer:
    """
    Traces Python file dependencies.

    Similar to @vercel/nft for Node.js, this class determines which files
    are necessary for a Python application to run by analyzing imports.
    """

    def __init__(self, options: TraceOptions | None = None):
        """
        Initialize the tracer.

        Args:
            options: Tracing options.
        """
        self.options = options or TraceOptions()
        self.file_list: set[str] = set()
        self.reasons: dict[str, FileReason] = {}
        self.warnings: list[str] = []
        self._processed: set[str] = set()
        self._stdlib_paths = get_stdlib_paths()
        self._site_packages_paths = get_site_packages_paths()
        self._search_paths: list[Path] = []
        self._current_depth = 0

    def trace(self, files: list[str | Path]) -> TraceResult:
        """
        Trace all dependencies starting from the given files.

        Args:
            files: List of entry point files to trace.

        Returns:
            TraceResult containing all traced files and reasons.
        """
        base = self.options.base or Path.cwd()
        if not base.is_absolute():
            base = Path.cwd() / base
        base = base.resolve()

        # Build search paths
        self._search_paths = self._build_search_paths(base)

        # Process each initial file
        for file_path in files:
            path = Path(file_path)
            if not path.is_absolute():
                # Resolve relative to cwd, not base
                path = Path.cwd() / path
            path = path.resolve()

            if path.is_file():
                self._emit_file(path, FileType.INITIAL, parent=None)

        return TraceResult(
            file_list=self.file_list.copy(),
            reasons=self.reasons.copy(),
            warnings=self.warnings.copy(),
            base=base,
        )

    def _build_search_paths(self, base: Path) -> list[Path]:
        """Build the list of paths to search for modules."""
        paths = [base]

        # Add current directory's src if it exists
        src_dir = base / "src"
        if src_dir.is_dir():
            paths.append(src_dir)

        # Add sys.path entries
        for p in sys.path:
            if p:
                path = Path(p)
                if path.is_dir() and path not in paths:
                    paths.append(path)

        return paths

    def _should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored based on options."""
        path_str = str(path)
        for pattern in self.options.ignore:
            if fnmatch.fnmatch(path_str, pattern):
                return True
            if fnmatch.fnmatch(path.name, pattern):
                return True
        return False

    def _should_include(self, path: Path) -> bool:
        """Check if a path should be included based on options."""
        if self._should_ignore(path):
            return False

        # Check stdlib
        if is_stdlib_path(path, self._stdlib_paths):
            return self.options.include_stdlib

        # Check site-packages
        if is_site_packages_path(path, self._site_packages_paths):
            return self.options.include_site_packages

        return True

    def _emit_file(
        self,
        path: Path,
        file_type: FileType,
        parent: str | None,
        module_name: str | None = None,
    ) -> None:
        """
        Add a file to the trace results and process its dependencies.

        Args:
            path: Path to the file.
            file_type: Type of file (initial, import, etc.).
            parent: Path of the file that imported this one.
            module_name: The module name used in the import.
        """
        path_str = str(path)

        # Check max depth
        if self.options.max_depth is not None:
            if self._current_depth > self.options.max_depth:
                return

        # Skip if already fully processed
        if path_str in self._processed:
            # Still add the parent relationship
            if parent and path_str in self.reasons:
                self.reasons[path_str].add_parent(parent)
            return

        # Check if we should include this file
        if not self._should_include(path):
            if path_str not in self.reasons:
                self.reasons[path_str] = FileReason(
                    type=file_type,
                    ignored=True,
                    module_name=module_name,
                )
            if parent:
                self.reasons[path_str].add_parent(parent)
            return

        # Add to file list and reasons
        self.file_list.add(path_str)

        if path_str not in self.reasons:
            self.reasons[path_str] = FileReason(
                type=file_type,
                module_name=module_name,
            )
        if parent:
            self.reasons[path_str].add_parent(parent)

        # Mark as processed before recursing to prevent cycles
        self._processed.add(path_str)

        # Only analyze Python files
        if path.suffix == ".py" and path.is_file():
            self._current_depth += 1
            self._process_imports(path)
            self._current_depth -= 1

    def _process_imports(self, file_path: Path) -> None:
        """
        Process all imports in a Python file.

        Args:
            file_path: Path to the Python file.
        """
        imports = analyze_file(file_path)

        for import_info in imports:
            self._process_import(import_info, file_path)

        # Handle dynamic imports if enabled
        if self.options.follow_dynamic_imports:
            try:
                source = file_path.read_text(encoding="utf-8")
                dynamic = extract_dynamic_imports(source)
                for module_name in dynamic:
                    fake_import = ImportInfo(
                        module=module_name,
                        names=[],
                        is_from_import=False,
                        level=0,
                        lineno=0,
                    )
                    self._process_import(fake_import, file_path)
            except (OSError, UnicodeDecodeError):
                pass

    def _process_import(self, import_info: ImportInfo, from_file: Path) -> None:
        """
        Process a single import and add its target to the trace.

        Args:
            import_info: Information about the import.
            from_file: The file containing the import.
        """
        resolved = resolve_import(
            import_info,
            from_file,
            self._search_paths,
        )

        if resolved is None:
            # Could not resolve the import
            module_name = import_info.module
            if import_info.level > 0:
                module_name = f"{'.' * import_info.level}{import_info.module}"
            self.warnings.append(
                f"Could not resolve import '{module_name}' in {from_file}"
            )
            return

        # Handle directory (package) vs file
        if resolved.is_dir():
            # This is a namespace package or package directory
            init_file = resolved / "__init__.py"
            if init_file.is_file():
                self._emit_file(
                    init_file,
                    FileType.PACKAGE,
                    parent=str(from_file),
                    module_name=import_info.module,
                )
        elif resolved.name == "__init__.py":
            # This is a package __init__.py file
            self._emit_file(
                resolved,
                FileType.PACKAGE,
                parent=str(from_file),
                module_name=import_info.module,
            )
        else:
            self._emit_file(
                resolved,
                FileType.IMPORT,
                parent=str(from_file),
                module_name=import_info.module,
            )

        # If importing specific names from a package, those might be submodules
        if import_info.is_from_import and import_info.names:
            self._resolve_from_imports(
                import_info,
                resolved,
                from_file,
            )

    def _resolve_from_imports(
        self,
        import_info: ImportInfo,
        resolved_base: Path,
        from_file: Path,
    ) -> None:
        """
        Resolve 'from X import a, b, c' where a, b, c might be submodules.

        Args:
            import_info: The import information.
            resolved_base: The resolved base module/package path.
            from_file: The file containing the import.
        """
        # Get the package directory
        if resolved_base.is_file():
            if resolved_base.name == "__init__.py":
                package_dir = resolved_base.parent
            else:
                return  # Not a package, names are attributes
        else:
            package_dir = resolved_base

        # Check each imported name as a potential submodule
        for name in import_info.names:
            if name == "*":
                continue

            # Check for submodule
            submodule_file = package_dir / f"{name}.py"
            if submodule_file.is_file():
                self._emit_file(
                    submodule_file.resolve(),
                    FileType.IMPORT,
                    parent=str(from_file),
                    module_name=f"{import_info.module}.{name}" if import_info.module else name,
                )

            # Check for subpackage
            subpackage_init = package_dir / name / "__init__.py"
            if subpackage_init.is_file():
                self._emit_file(
                    subpackage_init.resolve(),
                    FileType.PACKAGE,
                    parent=str(from_file),
                    module_name=f"{import_info.module}.{name}" if import_info.module else name,
                )


def python_file_trace(
    files: list[str | Path],
    options: TraceOptions | None = None,
) -> TraceResult:
    """
    Trace Python file dependencies.

    Determines which files are necessary for a Python application to run
    by analyzing import statements.

    Args:
        files: Entry point files to trace from.
        options: Tracing options.

    Returns:
        TraceResult containing all traced files and metadata.

    Example:
        >>> result = python_file_trace(["./main.py"])
        >>> print(result.file_list)
        {'./main.py', './utils.py', './models/__init__.py', ...}
    """
    tracer = Tracer(options)
    return tracer.trace(files)
