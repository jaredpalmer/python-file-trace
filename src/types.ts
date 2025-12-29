/**
 * Represents the type of file inclusion reason
 */
export type ReasonType =
  | 'input'      // Initial input file
  | 'import'     // Standard import statement
  | 'from'       // from x import y
  | 'dynamic'    // Dynamic import (__import__, importlib)
  | 'asset'      // Non-Python asset file
  | 'package'    // Package __init__.py
  | 'relative'   // Relative import
  | 'namespace'  // Namespace package

/**
 * Reason for including a file in the trace
 */
export interface FileReason {
  type: ReasonType;
  parents: Set<string>;
  moduleName?: string;
  ignored?: boolean;
}

/**
 * Options for pythonFileTrace
 */
export interface PythonFileTraceOptions {
  /**
   * Base directory for resolving relative paths
   * @default process.cwd()
   */
  base?: string;

  /**
   * Python executable to use for AST parsing
   * @default 'python3'
   */
  pythonPath?: string;

  /**
   * Additional paths to search for modules (like PYTHONPATH)
   */
  modulePaths?: string[];

  /**
   * Whether to follow symbolic links
   * @default true
   */
  followSymlinks?: boolean;

  /**
   * Glob patterns to ignore
   */
  ignore?: string[];

  /**
   * Maximum depth for recursive tracing
   * @default 100
   */
  maxDepth?: number;

  /**
   * Custom file read function
   */
  readFile?: (path: string) => Promise<string>;

  /**
   * Custom stat function
   */
  stat?: (path: string) => Promise<{ isFile: boolean; isDirectory: boolean; isSymlink: boolean }>;

  /**
   * Whether to include standard library modules
   * @default false
   */
  includeStdlib?: boolean;

  /**
   * Cache object for reusing across multiple traces
   */
  cache?: TraceCache;

  /**
   * File I/O concurrency limit
   * @default 1024
   */
  fileIOConcurrency?: number;

  /**
   * Whether to analyze dynamic imports
   * @default true
   */
  analyzeDynamic?: boolean;
}

/**
 * Cache for trace operations
 */
export interface TraceCache {
  fileContents: Map<string, string>;
  parsedImports: Map<string, ParsedImports>;
  resolvedModules: Map<string, string | null>;
  stdlibModules: Set<string>;
}

/**
 * Parsed import information from a Python file
 */
export interface ParsedImports {
  imports: ImportInfo[];
  fromImports: FromImportInfo[];
  dynamicImports: DynamicImportInfo[];
}

/**
 * Standard import statement: import x, import x.y
 */
export interface ImportInfo {
  module: string;
  alias?: string;
  line: number;
}

/**
 * From import statement: from x import y
 */
export interface FromImportInfo {
  module: string;
  names: Array<{ name: string; alias?: string }>;
  level: number; // Relative import level (0 = absolute, 1 = ., 2 = .., etc.)
  line: number;
}

/**
 * Dynamic import: __import__(), importlib.import_module()
 */
export interface DynamicImportInfo {
  type: 'builtin' | 'importlib';
  module?: string; // Only if statically analyzable
  line: number;
  expression?: string; // The raw expression if not statically analyzable
}

/**
 * Result of pythonFileTrace
 */
export interface PythonFileTraceResult {
  /**
   * Set of all files needed to run the application
   */
  fileList: Set<string>;

  /**
   * Detailed reasons for each file's inclusion
   */
  reasons: Map<string, FileReason>;

  /**
   * Any warnings encountered during tracing
   */
  warnings: string[];

  /**
   * Files that could not be resolved
   */
  unresolved: Map<string, string[]>;
}

/**
 * Python environment information
 */
export interface PythonEnv {
  version: string;
  sysPath: string[];
  stdlibPath: string;
  sitePackages: string[];
}
