import { readFile as fsReadFile } from 'node:fs/promises';
import { resolve, relative, isAbsolute, dirname } from 'node:path';
import { minimatch } from 'minimatch';
import type {
  PythonFileTraceOptions,
  PythonFileTraceResult,
  FileReason,
  TraceCache,
  ParsedImports,
} from './types.js';
import { parseImports, getPythonEnv, getStdlibModules, parseImportsRegex } from './parser.js';
import { createResolver, type Resolver } from './resolver.js';

interface TraceContext {
  options: Required<
    Pick<
      PythonFileTraceOptions,
      | 'base'
      | 'pythonPath'
      | 'modulePaths'
      | 'followSymlinks'
      | 'maxDepth'
      | 'includeStdlib'
      | 'fileIOConcurrency'
      | 'analyzeDynamic'
    >
  > &
    PythonFileTraceOptions;
  resolver: Resolver;
  cache: TraceCache;
  fileList: Set<string>;
  reasons: Map<string, FileReason>;
  warnings: string[];
  unresolved: Map<string, string[]>;
  pending: Set<string>;
  traced: Set<string>; // Files that have been fully traced
  semaphore: Semaphore;
}

/**
 * Simple semaphore for limiting concurrent operations
 */
class Semaphore {
  private queue: Array<() => void> = [];
  private current = 0;

  constructor(private max: number) {}

  async acquire(): Promise<void> {
    if (this.current < this.max) {
      this.current++;
      return;
    }

    return new Promise((resolve) => {
      this.queue.push(resolve);
    });
  }

  release(): void {
    this.current--;
    const next = this.queue.shift();
    if (next) {
      this.current++;
      next();
    }
  }

  async run<T>(fn: () => Promise<T>): Promise<T> {
    await this.acquire();
    try {
      return await fn();
    } finally {
      this.release();
    }
  }
}

/**
 * Create or use existing cache
 */
function createCache(existing?: TraceCache): TraceCache {
  return existing ?? {
    fileContents: new Map(),
    parsedImports: new Map(),
    resolvedModules: new Map(),
    stdlibModules: new Set(),
  };
}

/**
 * Read a file with caching
 */
async function readFile(
  path: string,
  ctx: TraceContext
): Promise<string> {
  const cached = ctx.cache.fileContents.get(path);
  if (cached !== undefined) return cached;

  const content = ctx.options.readFile
    ? await ctx.options.readFile(path)
    : await fsReadFile(path, 'utf-8');

  ctx.cache.fileContents.set(path, content);
  return content;
}

/**
 * Parse imports with caching
 */
async function getImports(
  path: string,
  content: string,
  ctx: TraceContext
): Promise<ParsedImports> {
  const cached = ctx.cache.parsedImports.get(path);
  if (cached) return cached;

  let imports: ParsedImports;

  try {
    imports = await parseImports(content, {
      pythonPath: ctx.options.pythonPath,
    });
  } catch (e) {
    // Fallback to regex parser if Python is not available
    ctx.warnings.push(`Using regex parser for ${path}: ${e}`);
    imports = parseImportsRegex(content);
  }

  ctx.cache.parsedImports.set(path, imports);
  return imports;
}

/**
 * Check if a path should be ignored
 */
function shouldIgnore(path: string, ctx: TraceContext): boolean {
  if (!ctx.options.ignore) return false;

  const relativePath = relative(ctx.options.base, path);

  for (const pattern of ctx.options.ignore) {
    if (minimatch(relativePath, pattern)) return true;
    if (minimatch(path, pattern)) return true;
  }

  return false;
}

/**
 * Add a file to the trace result
 */
function addFile(
  path: string,
  type: FileReason['type'],
  parent: string | null,
  ctx: TraceContext,
  moduleName?: string
): void {
  const normalizedPath = resolve(path);

  if (!ctx.fileList.has(normalizedPath)) {
    ctx.fileList.add(normalizedPath);
    ctx.reasons.set(normalizedPath, {
      type,
      parents: new Set(parent ? [parent] : []),
      moduleName,
      ignored: shouldIgnore(normalizedPath, ctx),
    });
  } else {
    // File already exists, add parent
    const reason = ctx.reasons.get(normalizedPath)!;
    if (parent) {
      reason.parents.add(parent);
    }
  }
}

/**
 * Add an unresolved import
 */
function addUnresolved(
  moduleName: string,
  fromFile: string,
  ctx: TraceContext
): void {
  if (!ctx.unresolved.has(moduleName)) {
    ctx.unresolved.set(moduleName, []);
  }
  ctx.unresolved.get(moduleName)!.push(fromFile);
}

/**
 * Trace a single file and its imports
 */
async function traceFile(
  path: string,
  depth: number,
  ctx: TraceContext,
  isInput = false
): Promise<void> {
  const normalizedPath = resolve(path);

  // Check depth limit
  if (depth > ctx.options.maxDepth) {
    ctx.warnings.push(`Max depth exceeded for ${normalizedPath}`);
    return;
  }

  // Skip if already processing (pending prevents circular dependencies)
  if (ctx.pending.has(normalizedPath)) {
    return;
  }

  // Skip if already fully traced
  if (ctx.traced.has(normalizedPath)) {
    return;
  }

  ctx.pending.add(normalizedPath);

  // Add input files to the fileList
  if (isInput) {
    addFile(normalizedPath, 'input', null, ctx);
  }

  // Check ignore patterns
  if (shouldIgnore(normalizedPath, ctx)) {
    ctx.pending.delete(normalizedPath);
    return;
  }

  // Read and parse the file
  let content: string;
  try {
    content = await ctx.semaphore.run(() => readFile(normalizedPath, ctx));
  } catch (e) {
    ctx.warnings.push(`Failed to read ${normalizedPath}: ${e}`);
    ctx.pending.delete(normalizedPath);
    return;
  }

  const imports = await getImports(normalizedPath, content, ctx);

  // Process standard imports: import x, import x.y
  const importPromises: Promise<void>[] = [];

  for (const imp of imports.imports) {
    importPromises.push(
      (async () => {
        const resolved = await ctx.resolver.resolveModule(
          imp.module,
          normalizedPath
        );

        if (resolved) {
          addFile(resolved.path, 'import', normalizedPath, ctx, imp.module);

          if (!resolved.isNamespacePackage) {
            await traceFile(resolved.path, depth + 1, ctx);
          }
        } else if (!ctx.resolver.isStdlibModule(imp.module)) {
          addUnresolved(imp.module, normalizedPath, ctx);
        }
      })()
    );
  }

  // Process from imports: from x import y
  for (const imp of imports.fromImports) {
    importPromises.push(
      (async () => {
        let resolved;

        if (imp.level > 0) {
          // Relative import
          resolved = await ctx.resolver.resolveRelativeImport(
            imp.module,
            imp.level,
            normalizedPath
          );

          if (resolved) {
            addFile(
              resolved.path,
              'relative',
              normalizedPath,
              ctx,
              imp.module || '.'
            );

            if (!resolved.isNamespacePackage) {
              await traceFile(resolved.path, depth + 1, ctx);
            }

            // Check if imported names are submodules
            for (const name of imp.names) {
              if (name.name === '*') continue;

              const submodule = await ctx.resolver.resolveImportedName(
                resolved.path,
                name.name,
                resolved.isPackage
              );

              if (submodule) {
                addFile(
                  submodule.path,
                  'from',
                  normalizedPath,
                  ctx,
                  `${imp.module || '.'}.${name.name}`
                );

                if (!submodule.isNamespacePackage) {
                  await traceFile(submodule.path, depth + 1, ctx);
                }
              }
            }
          } else {
            const moduleName = '.'.repeat(imp.level) + (imp.module || '');
            addUnresolved(moduleName, normalizedPath, ctx);
          }
        } else {
          // Absolute import
          const fullModule = imp.module;

          if (fullModule) {
            resolved = await ctx.resolver.resolveModule(
              fullModule,
              normalizedPath
            );

            if (resolved) {
              addFile(resolved.path, 'from', normalizedPath, ctx, fullModule);

              if (!resolved.isNamespacePackage) {
                await traceFile(resolved.path, depth + 1, ctx);
              }

              // Check if imported names are submodules
              for (const name of imp.names) {
                if (name.name === '*') continue;

                const submodule = await ctx.resolver.resolveImportedName(
                  resolved.path,
                  name.name,
                  resolved.isPackage
                );

                if (submodule) {
                  addFile(
                    submodule.path,
                    'from',
                    normalizedPath,
                    ctx,
                    `${fullModule}.${name.name}`
                  );

                  if (!submodule.isNamespacePackage) {
                    await traceFile(submodule.path, depth + 1, ctx);
                  }
                }
              }
            } else if (!ctx.resolver.isStdlibModule(fullModule)) {
              addUnresolved(fullModule, normalizedPath, ctx);
            }
          }
        }
      })()
    );
  }

  // Process dynamic imports if enabled
  if (ctx.options.analyzeDynamic) {
    for (const imp of imports.dynamicImports) {
      if (imp.module) {
        importPromises.push(
          (async () => {
            const resolved = await ctx.resolver.resolveModule(
              imp.module!,
              normalizedPath
            );

            if (resolved) {
              addFile(resolved.path, 'dynamic', normalizedPath, ctx, imp.module);

              if (!resolved.isNamespacePackage) {
                await traceFile(resolved.path, depth + 1, ctx);
              }
            } else if (!ctx.resolver.isStdlibModule(imp.module!)) {
              addUnresolved(imp.module!, normalizedPath, ctx);
            }
          })()
        );
      } else if (imp.expression) {
        ctx.warnings.push(
          `Dynamic import with non-static expression at ${normalizedPath}:${imp.line}: ${imp.expression}`
        );
      }
    }
  }

  await Promise.all(importPromises);
  ctx.pending.delete(normalizedPath);
  ctx.traced.add(normalizedPath);
}

/**
 * Main entry point for tracing Python files
 */
export async function pythonFileTrace(
  files: string[],
  options: PythonFileTraceOptions = {}
): Promise<PythonFileTraceResult> {
  const base = options.base ?? process.cwd();

  // Get Python environment if needed
  let pythonEnv;
  let stdlibModules: Set<string>;

  try {
    pythonEnv = await getPythonEnv({ pythonPath: options.pythonPath });
    stdlibModules = options.cache?.stdlibModules.size
      ? options.cache.stdlibModules
      : await getStdlibModules({ pythonPath: options.pythonPath });
  } catch (e) {
    // Python not available, use empty stdlib set
    pythonEnv = undefined;
    stdlibModules = new Set();
  }

  // Create resolver
  const resolver = createResolver({
    base,
    modulePaths: options.modulePaths ?? [],
    pythonEnv,
    followSymlinks: options.followSymlinks ?? true,
    includeStdlib: options.includeStdlib ?? false,
    stdlibModules,
    stdlibPath: pythonEnv?.stdlibPath,
    sitePackages: pythonEnv?.sitePackages ?? [],
    stat: options.stat,
  });

  // Create context
  const cache = createCache(options.cache);
  cache.stdlibModules = stdlibModules;

  const ctx: TraceContext = {
    options: {
      base,
      pythonPath: options.pythonPath ?? 'python3',
      modulePaths: options.modulePaths ?? [],
      followSymlinks: options.followSymlinks ?? true,
      maxDepth: options.maxDepth ?? 100,
      includeStdlib: options.includeStdlib ?? false,
      fileIOConcurrency: options.fileIOConcurrency ?? 1024,
      analyzeDynamic: options.analyzeDynamic ?? true,
      ...options,
    },
    resolver,
    cache,
    fileList: new Set(),
    reasons: new Map(),
    warnings: [],
    unresolved: new Map(),
    pending: new Set(),
    traced: new Set(),
    semaphore: new Semaphore(options.fileIOConcurrency ?? 1024),
  };

  // Normalize input files (relative to cwd, not base)
  const normalizedFiles = files.map((f) =>
    isAbsolute(f) ? f : resolve(process.cwd(), f)
  );

  // Trace all input files (traceFile will add them to fileList)
  await Promise.all(normalizedFiles.map((f) => traceFile(f, 0, ctx, true)));

  return {
    fileList: ctx.fileList,
    reasons: ctx.reasons,
    warnings: ctx.warnings,
    unresolved: ctx.unresolved,
  };
}
