import { readdir, stat as fsStat, readlink } from 'node:fs/promises';
import { join, dirname, resolve, relative, isAbsolute } from 'node:path';
import type { PythonFileTraceOptions, PythonEnv } from './types.js';

interface ResolverOptions {
  base: string;
  modulePaths: string[];
  pythonEnv?: PythonEnv;
  followSymlinks: boolean;
  includeStdlib: boolean;
  stdlibModules: Set<string>;
  stdlibPath?: string;
  sitePackages: string[];
  stat?: PythonFileTraceOptions['stat'];
}

interface ResolveResult {
  path: string;
  isPackage: boolean;
  isNamespacePackage: boolean;
}

/**
 * Creates a Python module resolver
 */
export function createResolver(options: ResolverOptions) {
  const {
    base,
    modulePaths,
    pythonEnv,
    followSymlinks,
    includeStdlib,
    stdlibModules,
    stdlibPath,
    sitePackages,
    stat: customStat,
  } = options;

  // Build the search path order (similar to sys.path)
  const searchPaths: string[] = [
    base,
    ...modulePaths,
    ...sitePackages,
  ];

  // Add stdlib path if including stdlib
  if (includeStdlib && stdlibPath) {
    searchPaths.push(stdlibPath);
  }

  async function statPath(filePath: string): Promise<{
    isFile: boolean;
    isDirectory: boolean;
    isSymlink: boolean;
  } | null> {
    try {
      if (customStat) {
        return await customStat(filePath);
      }

      const stats = await fsStat(filePath);
      let isSymlink = false;

      if (followSymlinks) {
        try {
          await readlink(filePath);
          isSymlink = true;
        } catch {
          // Not a symlink
        }
      }

      return {
        isFile: stats.isFile(),
        isDirectory: stats.isDirectory(),
        isSymlink,
      };
    } catch {
      return null;
    }
  }

  /**
   * Check if a path is a Python file
   */
  async function isPythonFile(filePath: string): Promise<boolean> {
    if (!filePath.endsWith('.py')) return false;
    const stats = await statPath(filePath);
    return stats?.isFile ?? false;
  }

  /**
   * Check if a path is a Python package (directory with __init__.py)
   */
  async function isPackage(dirPath: string): Promise<boolean> {
    const initPath = join(dirPath, '__init__.py');
    const stats = await statPath(initPath);
    return stats?.isFile ?? false;
  }

  /**
   * Check if a path is a namespace package (directory without __init__.py, PEP 420)
   */
  async function isNamespacePackage(dirPath: string): Promise<boolean> {
    const stats = await statPath(dirPath);
    if (!stats?.isDirectory) return false;

    // It's a namespace package if it's a directory without __init__.py
    // but contains Python files or subdirectories
    const initStats = await statPath(join(dirPath, '__init__.py'));
    if (initStats?.isFile) return false;

    try {
      const entries = await readdir(dirPath);
      for (const entry of entries) {
        const entryPath = join(dirPath, entry);
        const entryStats = await statPath(entryPath);
        if (entryStats?.isFile && entry.endsWith('.py')) return true;
        if (entryStats?.isDirectory) return true;
      }
    } catch {
      return false;
    }

    return false;
  }

  /**
   * Check if a module is in the standard library
   */
  function isStdlibModule(moduleName: string): boolean {
    const topLevel = moduleName.split('.')[0];
    return stdlibModules.has(topLevel);
  }

  /**
   * Resolve a module name to a file path
   */
  async function resolveModule(
    moduleName: string,
    fromFile?: string
  ): Promise<ResolveResult | null> {
    // Check if this is a stdlib module and we're not including stdlib
    if (!includeStdlib && isStdlibModule(moduleName)) {
      return null;
    }

    const parts = moduleName.split('.');

    // Build search paths, prioritizing the directory of the importing file
    const paths = fromFile
      ? [dirname(fromFile), ...searchPaths]
      : searchPaths;

    for (const searchPath of paths) {
      const result = await resolveInPath(parts, searchPath);
      if (result) return result;
    }

    return null;
  }

  /**
   * Resolve module parts within a search path
   */
  async function resolveInPath(
    parts: string[],
    basePath: string
  ): Promise<ResolveResult | null> {
    let currentPath = basePath;

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      const isLast = i === parts.length - 1;

      // Try as a module file
      const modulePath = join(currentPath, `${part}.py`);
      const moduleStats = await statPath(modulePath);

      if (moduleStats?.isFile && isLast) {
        return {
          path: modulePath,
          isPackage: false,
          isNamespacePackage: false,
        };
      }

      // Try as a package directory
      const packagePath = join(currentPath, part);
      const packageStats = await statPath(packagePath);

      if (packageStats?.isDirectory) {
        if (isLast) {
          // Check if it's a regular package
          const initPath = join(packagePath, '__init__.py');
          const initStats = await statPath(initPath);

          if (initStats?.isFile) {
            return {
              path: initPath,
              isPackage: true,
              isNamespacePackage: false,
            };
          }

          // Check if it's a namespace package
          if (await isNamespacePackage(packagePath)) {
            return {
              path: packagePath,
              isPackage: true,
              isNamespacePackage: true,
            };
          }
        }

        currentPath = packagePath;
      } else {
        return null;
      }
    }

    return null;
  }

  /**
   * Resolve a relative import
   */
  async function resolveRelativeImport(
    moduleName: string,
    level: number,
    fromFile: string
  ): Promise<ResolveResult | null> {
    // Start from the directory of the importing file
    let basePath = dirname(fromFile);

    // Go up 'level - 1' directories (level 1 = current package)
    for (let i = 1; i < level; i++) {
      basePath = dirname(basePath);
    }

    if (!moduleName) {
      // from . import x - return the package's __init__.py
      const initPath = join(basePath, '__init__.py');
      const initStats = await statPath(initPath);

      if (initStats?.isFile) {
        return {
          path: initPath,
          isPackage: true,
          isNamespacePackage: false,
        };
      }

      return null;
    }

    const parts = moduleName.split('.');
    return await resolveInPath(parts, basePath);
  }

  /**
   * Resolve an imported name from a module
   * For "from x import y", we need to check if y is a submodule
   */
  async function resolveImportedName(
    modulePath: string,
    name: string,
    isPackageImport: boolean
  ): Promise<ResolveResult | null> {
    if (!isPackageImport) {
      return null;
    }

    // The module path is __init__.py, get the package directory
    const packageDir = dirname(modulePath);

    // Try as a submodule
    const submodulePath = join(packageDir, `${name}.py`);
    const submoduleStats = await statPath(submodulePath);

    if (submoduleStats?.isFile) {
      return {
        path: submodulePath,
        isPackage: false,
        isNamespacePackage: false,
      };
    }

    // Try as a subpackage
    const subpackagePath = join(packageDir, name);
    const subpackageStats = await statPath(subpackagePath);

    if (subpackageStats?.isDirectory) {
      const initPath = join(subpackagePath, '__init__.py');
      const initStats = await statPath(initPath);

      if (initStats?.isFile) {
        return {
          path: initPath,
          isPackage: true,
          isNamespacePackage: false,
        };
      }

      if (await isNamespacePackage(subpackagePath)) {
        return {
          path: subpackagePath,
          isPackage: true,
          isNamespacePackage: true,
        };
      }
    }

    return null;
  }

  /**
   * Get all Python files in a package directory
   */
  async function getPackageFiles(packagePath: string): Promise<string[]> {
    const files: string[] = [];

    try {
      const entries = await readdir(packagePath);

      for (const entry of entries) {
        const entryPath = join(packagePath, entry);
        const entryStats = await statPath(entryPath);

        if (entryStats?.isFile && entry.endsWith('.py')) {
          files.push(entryPath);
        }
      }
    } catch {
      // Directory not readable
    }

    return files;
  }

  return {
    resolveModule,
    resolveRelativeImport,
    resolveImportedName,
    getPackageFiles,
    isStdlibModule,
    isPythonFile,
    isPackage,
  };
}

export type Resolver = ReturnType<typeof createResolver>;
