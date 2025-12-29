import { describe, it, expect, beforeAll } from 'vitest';
import { join, resolve } from 'node:path';
import { pythonFileTrace } from '../src/trace.js';
import { parseImports, parseImportsRegex } from '../src/parser.js';

const fixturesDir = join(__dirname, 'fixtures');

describe('pythonFileTrace', () => {
  describe('simple imports', () => {
    it('should trace simple module imports', async () => {
      const mainFile = join(fixturesDir, 'simple', 'main.py');
      const result = await pythonFileTrace([mainFile], {
        base: join(fixturesDir, 'simple'),
      });

      // Check that all files are included
      const filePaths = Array.from(result.fileList);
      const fileNames = filePaths.map((p) => p.split('/').pop());

      expect(fileNames).toContain('main.py');
      expect(fileNames).toContain('utils.py');
      expect(fileNames).toContain('helpers.py');
    });

    it('should track reasons for each file', async () => {
      const mainFile = join(fixturesDir, 'simple', 'main.py');
      const result = await pythonFileTrace([mainFile], {
        base: join(fixturesDir, 'simple'),
      });

      // Main file should be an input
      const mainReason = result.reasons.get(resolve(mainFile));
      expect(mainReason?.type).toBe('input');

      // Utils should be imported
      const utilsPath = Array.from(result.fileList).find((p) =>
        p.endsWith('utils.py')
      );
      expect(utilsPath).toBeDefined();
      if (utilsPath) {
        const utilsReason = result.reasons.get(utilsPath);
        expect(utilsReason?.type).toBe('import');
        expect(utilsReason?.parents.has(resolve(mainFile))).toBe(true);
      }
    });
  });

  describe('package imports', () => {
    it('should trace package imports including __init__.py', async () => {
      const mainFile = join(fixturesDir, 'package', 'main.py');
      const result = await pythonFileTrace([mainFile], {
        base: join(fixturesDir, 'package'),
      });

      const filePaths = Array.from(result.fileList);
      const fileNames = filePaths.map((p) => p.split('/').pop());

      expect(fileNames).toContain('main.py');
      expect(fileNames).toContain('__init__.py');
      expect(fileNames).toContain('module_a.py');
      expect(fileNames).toContain('module_b.py');
    });

    it('should handle from package import module', async () => {
      const mainFile = join(fixturesDir, 'package', 'main.py');
      const result = await pythonFileTrace([mainFile], {
        base: join(fixturesDir, 'package'),
      });

      // module_a should be included via "from mypackage import module_a"
      const moduleAPath = Array.from(result.fileList).find((p) =>
        p.endsWith('module_a.py')
      );
      expect(moduleAPath).toBeDefined();
    });
  });

  describe('relative imports', () => {
    it('should trace relative imports within packages', async () => {
      const mainFile = join(fixturesDir, 'relative', 'main.py');
      const result = await pythonFileTrace([mainFile], {
        base: join(fixturesDir, 'relative'),
      });

      const filePaths = Array.from(result.fileList);
      const fileNames = filePaths.map((p) => p.split('/').pop());

      expect(fileNames).toContain('main.py');
      expect(fileNames).toContain('entry.py');
      expect(fileNames).toContain('helper.py');
    });

    it('should handle deeply nested relative imports', async () => {
      const mainFile = join(fixturesDir, 'relative', 'main.py');
      const result = await pythonFileTrace([mainFile], {
        base: join(fixturesDir, 'relative'),
      });

      const filePaths = Array.from(result.fileList);
      const fileNames = filePaths.map((p) => p.split('/').pop());

      // deep.py should be included via nested relative imports
      expect(fileNames).toContain('deep.py');
    });
  });

  describe('dynamic imports', () => {
    it('should trace statically analyzable dynamic imports', async () => {
      const mainFile = join(fixturesDir, 'dynamic', 'main.py');
      const result = await pythonFileTrace([mainFile], {
        base: join(fixturesDir, 'dynamic'),
        analyzeDynamic: true,
      });

      const filePaths = Array.from(result.fileList);
      const fileNames = filePaths.map((p) => p.split('/').pop());

      expect(fileNames).toContain('main.py');
      expect(fileNames).toContain('static_module.py');
      expect(fileNames).toContain('another_module.py');
    });

    it('should warn about non-static dynamic imports', async () => {
      const mainFile = join(fixturesDir, 'dynamic', 'main.py');
      const result = await pythonFileTrace([mainFile], {
        base: join(fixturesDir, 'dynamic'),
        analyzeDynamic: true,
      });

      // Should have a warning about the dynamic module_name variable
      expect(result.warnings.some((w) => w.includes('module_name'))).toBe(true);
    });

    it('should skip dynamic import analysis when disabled', async () => {
      const mainFile = join(fixturesDir, 'dynamic', 'main.py');
      const result = await pythonFileTrace([mainFile], {
        base: join(fixturesDir, 'dynamic'),
        analyzeDynamic: false,
      });

      const filePaths = Array.from(result.fileList);
      const fileNames = filePaths.map((p) => p.split('/').pop());

      // Static imports should still be traced
      expect(fileNames).toContain('main.py');
      // Dynamic imports should not be traced
      expect(fileNames).not.toContain('static_module.py');
      expect(fileNames).not.toContain('another_module.py');
    });
  });

  describe('options', () => {
    it('should respect ignore patterns', async () => {
      const mainFile = join(fixturesDir, 'simple', 'main.py');
      const result = await pythonFileTrace([mainFile], {
        base: join(fixturesDir, 'simple'),
        ignore: ['**/helpers.py'],
      });

      const filePaths = Array.from(result.fileList);
      const fileNames = filePaths.map((p) => p.split('/').pop());

      expect(fileNames).toContain('main.py');
      expect(fileNames).toContain('utils.py');
      // helpers.py should be ignored
      expect(
        filePaths.some(
          (p) => p.endsWith('helpers.py') && !result.reasons.get(p)?.ignored
        )
      ).toBe(false);
    });

    it('should track unresolved imports', async () => {
      const mainFile = join(fixturesDir, 'simple', 'main.py');
      const result = await pythonFileTrace([mainFile], {
        base: join(fixturesDir, 'simple'),
        includeStdlib: false, // Don't include stdlib
      });

      // os, json, etc. from stdlib should not be in unresolved
      // but any non-existent local modules would be
    });

    it('should use cache across multiple traces', async () => {
      const cache = {
        fileContents: new Map(),
        parsedImports: new Map(),
        resolvedModules: new Map(),
        stdlibModules: new Set<string>(),
      };

      const mainFile = join(fixturesDir, 'simple', 'main.py');

      // First trace
      await pythonFileTrace([mainFile], {
        base: join(fixturesDir, 'simple'),
        cache,
      });

      // Cache should be populated
      expect(cache.fileContents.size).toBeGreaterThan(0);
      expect(cache.parsedImports.size).toBeGreaterThan(0);

      // Second trace should use cache
      const result2 = await pythonFileTrace([mainFile], {
        base: join(fixturesDir, 'simple'),
        cache,
      });

      expect(result2.fileList.size).toBeGreaterThan(0);
    });
  });
});

describe('parseImports', () => {
  it('should parse standard imports', async () => {
    const source = `
import os
import sys
import json as j
import foo.bar.baz
`;
    const result = await parseImports(source);

    expect(result.imports).toHaveLength(4);
    expect(result.imports[0]).toMatchObject({ module: 'os', line: 2 });
    expect(result.imports[1]).toMatchObject({ module: 'sys', line: 3 });
    expect(result.imports[2]).toMatchObject({
      module: 'json',
      alias: 'j',
      line: 4,
    });
    expect(result.imports[3]).toMatchObject({
      module: 'foo.bar.baz',
      line: 5,
    });
  });

  it('should parse from imports', async () => {
    const source = `
from os import path
from json import loads, dumps
from foo.bar import baz as b
`;
    const result = await parseImports(source);

    expect(result.fromImports).toHaveLength(3);
    expect(result.fromImports[0]).toMatchObject({
      module: 'os',
      level: 0,
    });
    expect(result.fromImports[0].names).toContainEqual({ name: 'path', alias: null });
    expect(result.fromImports[2].names).toContainEqual({
      name: 'baz',
      alias: 'b',
    });
  });

  it('should parse relative imports', async () => {
    const source = `
from . import sibling
from .. import parent
from ...pkg import module
from .subpkg import item
`;
    const result = await parseImports(source);

    expect(result.fromImports).toHaveLength(4);
    expect(result.fromImports[0]).toMatchObject({ module: '', level: 1 });
    expect(result.fromImports[1]).toMatchObject({ module: '', level: 2 });
    expect(result.fromImports[2]).toMatchObject({ module: 'pkg', level: 3 });
    expect(result.fromImports[3]).toMatchObject({
      module: 'subpkg',
      level: 1,
    });
  });

  it('should parse dynamic imports', async () => {
    const source = `
mod1 = __import__('mymodule')
mod2 = importlib.import_module('another')
`;
    const result = await parseImports(source);

    expect(result.dynamicImports).toHaveLength(2);
    expect(result.dynamicImports[0]).toMatchObject({
      type: 'builtin',
      module: 'mymodule',
    });
    expect(result.dynamicImports[1]).toMatchObject({
      type: 'importlib',
      module: 'another',
    });
  });
});

describe('parseImportsRegex', () => {
  it('should parse standard imports with regex fallback', () => {
    const source = `
import os
import sys
import json as j
`;
    const result = parseImportsRegex(source);

    expect(result.imports).toHaveLength(3);
    expect(result.imports[0]).toMatchObject({ module: 'os' });
    expect(result.imports[1]).toMatchObject({ module: 'sys' });
    expect(result.imports[2]).toMatchObject({ module: 'json', alias: 'j' });
  });

  it('should parse from imports with regex fallback', () => {
    const source = `
from os import path
from json import loads, dumps
`;
    const result = parseImportsRegex(source);

    expect(result.fromImports).toHaveLength(2);
    expect(result.fromImports[0].names).toContainEqual({ name: 'path' });
  });

  it('should parse relative imports with regex fallback', () => {
    const source = `
from . import sibling
from .. import parent
`;
    const result = parseImportsRegex(source);

    expect(result.fromImports).toHaveLength(2);
    expect(result.fromImports[0]).toMatchObject({ level: 1 });
    expect(result.fromImports[1]).toMatchObject({ level: 2 });
  });
});
