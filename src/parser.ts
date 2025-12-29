import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { readFile } from 'node:fs/promises';
import type { ParsedImports, PythonEnv } from './types.js';

const currentFilePath = fileURLToPath(import.meta.url);
const currentDirPath = dirname(currentFilePath);

// Path to the Python parser script
const PARSER_SCRIPT = join(currentDirPath, 'python', 'parse_imports.py');

// Fallback path for development (before build)
const DEV_PARSER_SCRIPT = join(currentDirPath, '..', 'src', 'python', 'parse_imports.py');

interface PythonParserOptions {
  pythonPath?: string;
  timeout?: number;
}

/**
 * Execute a Python command and return the result
 */
async function execPython(
  command: string,
  input?: string,
  options: PythonParserOptions = {}
): Promise<string> {
  const pythonPath = options.pythonPath || 'python3';
  const timeout = options.timeout || 30000;

  // Try the installed path first, then fallback to dev path
  let scriptPath = PARSER_SCRIPT;
  try {
    await readFile(scriptPath);
  } catch {
    scriptPath = DEV_PARSER_SCRIPT;
  }

  return new Promise((resolve, reject) => {
    const proc = spawn(pythonPath, [scriptPath, command], {
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    let stdout = '';
    let stderr = '';

    const timer = setTimeout(() => {
      proc.kill();
      reject(new Error(`Python process timed out after ${timeout}ms`));
    }, timeout);

    proc.stdout.on('data', (data: Buffer) => {
      stdout += data.toString();
    });

    proc.stderr.on('data', (data: Buffer) => {
      stderr += data.toString();
    });

    proc.on('close', (code) => {
      clearTimeout(timer);
      if (code !== 0) {
        reject(new Error(`Python process exited with code ${code}: ${stderr}`));
      } else {
        resolve(stdout);
      }
    });

    proc.on('error', (err) => {
      clearTimeout(timer);
      reject(new Error(`Failed to spawn Python process: ${err.message}`));
    });

    if (input !== undefined) {
      proc.stdin.write(input);
      proc.stdin.end();
    }
  });
}

/**
 * Parse a Python source file and extract import information
 */
export async function parseImports(
  source: string,
  options: PythonParserOptions = {}
): Promise<ParsedImports> {
  const output = await execPython('parse', source, options);

  try {
    const result = JSON.parse(output);

    if (result.errors && result.errors.length > 0) {
      // Log errors but still return what we could parse
      for (const error of result.errors) {
        console.warn(`Parse warning at line ${error.line}: ${error.message}`);
      }
    }

    return {
      imports: result.imports || [],
      fromImports: result.fromImports || [],
      dynamicImports: result.dynamicImports || [],
    };
  } catch (e) {
    throw new Error(`Failed to parse Python parser output: ${output}`);
  }
}

/**
 * Get Python environment information
 */
export async function getPythonEnv(
  options: PythonParserOptions = {}
): Promise<PythonEnv> {
  const output = await execPython('env', undefined, options);

  try {
    return JSON.parse(output);
  } catch (e) {
    throw new Error(`Failed to parse Python env output: ${output}`);
  }
}

/**
 * Get the list of standard library modules
 */
export async function getStdlibModules(
  options: PythonParserOptions = {}
): Promise<Set<string>> {
  const output = await execPython('stdlib', undefined, options);

  try {
    const modules = JSON.parse(output);
    return new Set(modules);
  } catch (e) {
    throw new Error(`Failed to parse stdlib modules output: ${output}`);
  }
}

/**
 * Simple regex-based import parser as a fallback when Python is not available
 * This is less accurate but works without Python
 */
export function parseImportsRegex(source: string): ParsedImports {
  const imports: ParsedImports['imports'] = [];
  const fromImports: ParsedImports['fromImports'] = [];
  const dynamicImports: ParsedImports['dynamicImports'] = [];

  const lines = source.split('\n');

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    const lineNum = i + 1;

    // Skip comments and empty lines
    if (line.startsWith('#') || line === '') continue;

    // Match: import x, import x.y, import x as y
    const importMatch = line.match(/^import\s+([\w.]+)(?:\s+as\s+(\w+))?/);
    if (importMatch) {
      imports.push({
        module: importMatch[1],
        alias: importMatch[2] || undefined,
        line: lineNum,
      });
      continue;
    }

    // Match: from x import y, from . import y, from ..x import y
    const fromMatch = line.match(
      /^from\s+(\.*)(\w[\w.]*)?(?:\s+import\s+(.+))?/
    );
    if (fromMatch && line.includes('import')) {
      const level = fromMatch[1].length;
      const modulePart = fromMatch[2] || '';

      // Parse the imported names
      const namesStr = line.split('import')[1]?.trim() || '';
      const names: Array<{ name: string; alias?: string }> = [];

      // Handle parentheses for multi-line imports (simplified)
      const cleanedNames = namesStr.replace(/[()]/g, '');

      for (const part of cleanedNames.split(',')) {
        const trimmed = part.trim();
        if (!trimmed) continue;

        const asMatch = trimmed.match(/(\w+)\s+as\s+(\w+)/);
        if (asMatch) {
          names.push({ name: asMatch[1], alias: asMatch[2] });
        } else if (/^\w+$/.test(trimmed)) {
          names.push({ name: trimmed });
        }
      }

      if (names.length > 0) {
        fromImports.push({
          module: modulePart,
          names,
          level,
          line: lineNum,
        });
      }
      continue;
    }

    // Match: __import__('module')
    const builtinImportMatch = line.match(/__import__\s*\(\s*['"]([^'"]+)['"]/);
    if (builtinImportMatch) {
      dynamicImports.push({
        type: 'builtin',
        module: builtinImportMatch[1],
        line: lineNum,
      });
      continue;
    }

    // Match: importlib.import_module('module')
    const importlibMatch = line.match(
      /importlib\.import_module\s*\(\s*['"]([^'"]+)['"]/
    );
    if (importlibMatch) {
      dynamicImports.push({
        type: 'importlib',
        module: importlibMatch[1],
        line: lineNum,
      });
    }
  }

  return { imports, fromImports, dynamicImports };
}
