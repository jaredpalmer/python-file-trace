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

  // For static imports, remove strings and docstrings to avoid false positives
  const cleanedSource = removeStringsAndComments(source);
  const cleanedLines = cleanedSource.split('\n');

  // Join lines with backslash continuation
  const joinedLines = joinContinuationLines(cleanedLines);

  for (let i = 0; i < joinedLines.length; i++) {
    const { line, originalLineNum } = joinedLines[i];
    const trimmedLine = line.trim();

    // Skip empty lines (comments already removed)
    if (trimmedLine === '') continue;

    // Handle comma-separated imports: import a, b, c
    const multiImportMatch = trimmedLine.match(/^import\s+(.+)/);
    if (multiImportMatch) {
      const importParts = multiImportMatch[1].split(',');
      for (const part of importParts) {
        const trimmed = part.trim();
        if (!trimmed) continue;

        // Match: module OR module as alias
        const moduleMatch = trimmed.match(/^([\w.]+)(?:\s+as\s+(\w+))?$/);
        if (moduleMatch) {
          imports.push({
            module: moduleMatch[1],
            alias: moduleMatch[2] || undefined,
            line: originalLineNum,
          });
        }
      }
      continue;
    }

    // Match: from x import y, from . import y, from ..x import y
    const fromMatch = trimmedLine.match(
      /^from\s+(\.*)(\w[\w.]*)?(?:\s+import\s+(.+))?/
    );
    if (fromMatch && trimmedLine.includes('import')) {
      const level = fromMatch[1].length;
      const modulePart = fromMatch[2] || '';

      // Parse the imported names
      const importIdx = trimmedLine.indexOf('import');
      const namesStr = trimmedLine.slice(importIdx + 6).trim();
      const names: Array<{ name: string; alias?: string }> = [];

      // Handle parentheses for multi-line imports
      const cleanedNames = namesStr.replace(/[()]/g, '');

      for (const part of cleanedNames.split(',')) {
        const trimmed = part.trim();
        if (!trimmed) continue;

        // Skip star imports
        if (trimmed === '*') {
          names.push({ name: '*' });
          continue;
        }

        const asMatch = trimmed.match(/^(\w+)\s+as\s+(\w+)$/);
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
          line: originalLineNum,
        });
      }
      continue;
    }
  }

  // For dynamic imports, scan the original source (we need the string arguments)
  // But still remove comments to avoid false positives
  const sourceWithoutComments = removeComments(source);
  const originalLines = sourceWithoutComments.split('\n');

  for (let i = 0; i < originalLines.length; i++) {
    const line = originalLines[i];
    const lineNum = i + 1;

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

    // Match: importlib.import_module('module') or aliased variants
    const importlibMatch = line.match(
      /(?:importlib|\w+)\.import_module\s*\(\s*['"]([^'"]+)['"]/
    );
    if (importlibMatch) {
      dynamicImports.push({
        type: 'importlib',
        module: importlibMatch[1],
        line: lineNum,
      });
      continue;
    }

    // Match: import_module('module') - direct call after from importlib import import_module
    const directImportModuleMatch = line.match(
      /\bimport_module\s*\(\s*['"]([^'"]+)['"]/
    );
    if (directImportModuleMatch && !line.includes('.import_module')) {
      dynamicImports.push({
        type: 'importlib',
        module: directImportModuleMatch[1],
        line: lineNum,
      });
    }
  }

  return { imports, fromImports, dynamicImports };
}

/**
 * Remove strings, docstrings, and comments from Python source to avoid false positives
 */
function removeStringsAndComments(source: string): string {
  let result = '';
  let i = 0;
  const len = source.length;

  while (i < len) {
    // Check for triple-quoted strings (docstrings)
    if (source.slice(i, i + 3) === '"""' || source.slice(i, i + 3) === "'''") {
      const quote = source.slice(i, i + 3);
      i += 3;
      // Skip until closing triple quote
      while (i < len && source.slice(i, i + 3) !== quote) {
        if (source[i] === '\n') {
          result += '\n'; // Preserve line numbers
        }
        i++;
      }
      i += 3; // Skip closing triple quote
      continue;
    }

    // Check for single/double quoted strings
    if (source[i] === '"' || source[i] === "'") {
      const quote = source[i];
      i++;
      // Skip until closing quote (handling escapes)
      while (i < len && source[i] !== quote) {
        if (source[i] === '\\' && i + 1 < len) {
          i += 2; // Skip escaped character
        } else if (source[i] === '\n') {
          result += '\n'; // Preserve line numbers
          i++;
        } else {
          i++;
        }
      }
      i++; // Skip closing quote
      continue;
    }

    // Check for comments
    if (source[i] === '#') {
      // Skip until end of line
      while (i < len && source[i] !== '\n') {
        i++;
      }
      continue;
    }

    result += source[i];
    i++;
  }

  return result;
}

/**
 * Remove only comments from Python source (preserves strings)
 */
function removeComments(source: string): string {
  let result = '';
  let i = 0;
  const len = source.length;
  let inString = false;
  let stringChar = '';
  let inTripleString = false;

  while (i < len) {
    // Check for triple-quoted strings
    if (!inString && (source.slice(i, i + 3) === '"""' || source.slice(i, i + 3) === "'''")) {
      const quote = source.slice(i, i + 3);
      result += quote;
      i += 3;
      inTripleString = true;
      // Find closing triple quote
      while (i < len) {
        if (source.slice(i, i + 3) === quote) {
          result += quote;
          i += 3;
          inTripleString = false;
          break;
        }
        result += source[i];
        i++;
      }
      continue;
    }

    // Check for single/double quoted strings
    if (!inString && (source[i] === '"' || source[i] === "'")) {
      stringChar = source[i];
      inString = true;
      result += source[i];
      i++;
      continue;
    }

    // Handle string content
    if (inString) {
      if (source[i] === '\\' && i + 1 < len) {
        result += source[i] + source[i + 1];
        i += 2;
        continue;
      }
      if (source[i] === stringChar) {
        inString = false;
      }
      result += source[i];
      i++;
      continue;
    }

    // Check for comments (only when not in a string)
    if (source[i] === '#') {
      // Skip until end of line
      while (i < len && source[i] !== '\n') {
        i++;
      }
      continue;
    }

    result += source[i];
    i++;
  }

  return result;
}

/**
 * Join lines that use backslash continuation
 */
function joinContinuationLines(lines: string[]): Array<{ line: string; originalLineNum: number }> {
  const result: Array<{ line: string; originalLineNum: number }> = [];
  let currentLine = '';
  let startLineNum = 1;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const lineNum = i + 1;

    if (currentLine === '') {
      startLineNum = lineNum;
    }

    // Check if line ends with backslash (continuation)
    if (line.trimEnd().endsWith('\\')) {
      currentLine += line.trimEnd().slice(0, -1) + ' ';
    } else {
      currentLine += line;
      result.push({ line: currentLine, originalLineNum: startLineNum });
      currentLine = '';
    }
  }

  // Handle any remaining content
  if (currentLine !== '') {
    result.push({ line: currentLine, originalLineNum: startLineNum });
  }

  return result;
}
