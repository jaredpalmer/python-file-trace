import { describe, it, expect } from 'bun:test';
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

  it('should parse comma-separated imports', () => {
    const source = `
import os, sys, json
import math, random as r
`;
    const result = parseImportsRegex(source);

    expect(result.imports).toHaveLength(5);
    expect(result.imports[0]).toMatchObject({ module: 'os' });
    expect(result.imports[1]).toMatchObject({ module: 'sys' });
    expect(result.imports[2]).toMatchObject({ module: 'json' });
    expect(result.imports[3]).toMatchObject({ module: 'math' });
    expect(result.imports[4]).toMatchObject({ module: 'random', alias: 'r' });
  });

  it('should parse imports with backslash continuation', () => {
    const source = `
import os, \\
    sys, \\
    json
`;
    const result = parseImportsRegex(source);

    expect(result.imports).toHaveLength(3);
    expect(result.imports[0]).toMatchObject({ module: 'os' });
    expect(result.imports[1]).toMatchObject({ module: 'sys' });
    expect(result.imports[2]).toMatchObject({ module: 'json' });
  });

  it('should ignore imports in strings', () => {
    const source = `
x = "import fake_module"
y = 'from another import thing'
import real_module
`;
    const result = parseImportsRegex(source);

    expect(result.imports).toHaveLength(1);
    expect(result.imports[0]).toMatchObject({ module: 'real_module' });
  });

  it('should ignore imports in docstrings', () => {
    const source = `
"""
Example:
    import example_in_docstring
    from docstring import thing
"""
import real_module
`;
    const result = parseImportsRegex(source);

    expect(result.imports).toHaveLength(1);
    expect(result.imports[0]).toMatchObject({ module: 'real_module' });
  });

  it('should ignore imports in comments', () => {
    const source = `
# import commented_module
# from commented import thing
import real_module
`;
    const result = parseImportsRegex(source);

    expect(result.imports).toHaveLength(1);
    expect(result.imports[0]).toMatchObject({ module: 'real_module' });
  });

  it('should parse import_module direct call', () => {
    const source = `
from importlib import import_module
mod = import_module('dynamic_mod')
`;
    const result = parseImportsRegex(source);

    expect(result.dynamicImports).toHaveLength(1);
    expect(result.dynamicImports[0]).toMatchObject({
      type: 'importlib',
      module: 'dynamic_mod',
    });
  });

  it('should parse aliased importlib', () => {
    const source = `
import importlib as il
mod = il.import_module('dynamic_mod')
`;
    const result = parseImportsRegex(source);

    expect(result.dynamicImports).toHaveLength(1);
    expect(result.dynamicImports[0]).toMatchObject({
      type: 'importlib',
      module: 'dynamic_mod',
    });
  });
});

describe('edge cases', () => {
  describe('AST parser edge cases', () => {
    it('should parse aliased importlib imports', async () => {
      const source = `
import importlib as il
mod = il.import_module('mymodule')
`;
      const result = await parseImports(source);

      expect(result.dynamicImports).toHaveLength(1);
      expect(result.dynamicImports[0]).toMatchObject({
        type: 'importlib',
        module: 'mymodule',
      });
    });

    it('should parse direct import_module calls', async () => {
      const source = `
from importlib import import_module
mod = import_module('mymodule')
`;
      const result = await parseImports(source);

      expect(result.dynamicImports).toHaveLength(1);
      expect(result.dynamicImports[0]).toMatchObject({
        type: 'importlib',
        module: 'mymodule',
      });
    });

    it('should parse import_module with package parameter', async () => {
      const source = `
import importlib
mod = importlib.import_module('.submodule', 'mypackage')
`;
      const result = await parseImports(source);

      expect(result.dynamicImports).toHaveLength(1);
      expect(result.dynamicImports[0]).toMatchObject({
        type: 'importlib',
        module: '.submodule',
        package: 'mypackage',
        level: 1,
      });
    });

    it('should parse import_module with keyword package parameter', async () => {
      const source = `
import importlib
mod = importlib.import_module('.submodule', package='mypackage')
`;
      const result = await parseImports(source);

      expect(result.dynamicImports).toHaveLength(1);
      expect(result.dynamicImports[0]).toMatchObject({
        type: 'importlib',
        module: '.submodule',
        package: 'mypackage',
        level: 1,
      });
    });

    it('should parse import_module with name keyword', async () => {
      const source = `
from importlib import import_module
mod = import_module(name='mymodule')
`;
      const result = await parseImports(source);

      expect(result.dynamicImports).toHaveLength(1);
      expect(result.dynamicImports[0]).toMatchObject({
        type: 'importlib',
        module: 'mymodule',
      });
    });

    it('should parse aliased import_module function', async () => {
      const source = `
from importlib import import_module as load_mod
mod = load_mod('mymodule')
`;
      const result = await parseImports(source);

      expect(result.dynamicImports).toHaveLength(1);
      expect(result.dynamicImports[0]).toMatchObject({
        type: 'importlib',
        module: 'mymodule',
      });
    });

    it('should parse try/except fallback imports', async () => {
      const source = `
try:
    import fast_module
except ImportError:
    import slow_module
`;
      const result = await parseImports(source);

      expect(result.imports).toHaveLength(2);
      expect(result.imports[0]).toMatchObject({ module: 'fast_module' });
      expect(result.imports[1]).toMatchObject({ module: 'slow_module' });
    });

    it('should parse conditional imports', async () => {
      const source = `
import platform
if platform.system() == 'Windows':
    import win_module
else:
    import unix_module
`;
      const result = await parseImports(source);

      expect(result.imports).toHaveLength(3);
      expect(result.imports.map(i => i.module)).toContain('platform');
      expect(result.imports.map(i => i.module)).toContain('win_module');
      expect(result.imports.map(i => i.module)).toContain('unix_module');
    });

    it('should parse __future__ imports', async () => {
      const source = `
from __future__ import annotations
from __future__ import division, print_function
`;
      const result = await parseImports(source);

      expect(result.fromImports).toHaveLength(2);
      expect(result.fromImports[0]).toMatchObject({ module: '__future__' });
      expect(result.fromImports[1]).toMatchObject({ module: '__future__' });
    });

    it('should parse comma-separated imports', async () => {
      const source = `
import os, sys, json
`;
      const result = await parseImports(source);

      expect(result.imports).toHaveLength(3);
      expect(result.imports[0]).toMatchObject({ module: 'os' });
      expect(result.imports[1]).toMatchObject({ module: 'sys' });
      expect(result.imports[2]).toMatchObject({ module: 'json' });
    });

    it('should handle star imports', async () => {
      const source = `
from os.path import *
`;
      const result = await parseImports(source);

      expect(result.fromImports).toHaveLength(1);
      expect(result.fromImports[0].names).toContainEqual({ name: '*', alias: null });
    });

    it('should handle deeply nested relative imports', async () => {
      const source = `
from .... import ancestor
from ....pkg.sub import module
`;
      const result = await parseImports(source);

      expect(result.fromImports).toHaveLength(2);
      expect(result.fromImports[0]).toMatchObject({ level: 4, module: '' });
      expect(result.fromImports[1]).toMatchObject({ level: 4, module: 'pkg.sub' });
    });
  });

  describe('tracing edge cases', () => {
    it('should trace aliased importlib dynamic imports', async () => {
      const mainFile = join(fixturesDir, 'edge_cases', 'main.py');
      const result = await pythonFileTrace([mainFile], {
        base: join(fixturesDir, 'edge_cases'),
        analyzeDynamic: true,
      });

      const filePaths = Array.from(result.fileList);
      const fileNames = filePaths.map((p) => p.split('/').pop());

      // Should include dynamic imports via aliased importlib and direct import_module
      expect(fileNames).toContain('aliased_target.py');
      expect(fileNames).toContain('direct_target.py');
      expect(fileNames).toContain('keyword_target.py');
    });

    it('should trace try/except fallback imports', async () => {
      const mainFile = join(fixturesDir, 'edge_cases', 'main.py');
      const result = await pythonFileTrace([mainFile], {
        base: join(fixturesDir, 'edge_cases'),
      });

      const filePaths = Array.from(result.fileList);
      const fileNames = filePaths.map((p) => p.split('/').pop());

      // Both try and except branches should be traced
      expect(fileNames).toContain('fast_module.py');
      expect(fileNames).toContain('slow_module.py');
    });

    it('should trace conditional imports', async () => {
      const mainFile = join(fixturesDir, 'edge_cases', 'main.py');
      const result = await pythonFileTrace([mainFile], {
        base: join(fixturesDir, 'edge_cases'),
      });

      const filePaths = Array.from(result.fileList);
      const fileNames = filePaths.map((p) => p.split('/').pop());

      // Both branches should be traced
      expect(fileNames).toContain('win_helper.py');
      expect(fileNames).toContain('unix_helper.py');
    });

    it('should trace imports inside functions', async () => {
      const mainFile = join(fixturesDir, 'edge_cases', 'main.py');
      const result = await pythonFileTrace([mainFile], {
        base: join(fixturesDir, 'edge_cases'),
      });

      const filePaths = Array.from(result.fileList);
      const fileNames = filePaths.map((p) => p.split('/').pop());

      expect(fileNames).toContain('extra_module.py');
    });

    it('should NOT trace imports in strings', async () => {
      const mainFile = join(fixturesDir, 'edge_cases', 'main.py');
      const result = await pythonFileTrace([mainFile], {
        base: join(fixturesDir, 'edge_cases'),
      });

      const filePaths = Array.from(result.fileList);
      const fileNames = filePaths.map((p) => p.split('/').pop());

      // Fake modules in strings should not be traced
      expect(fileNames).not.toContain('fake_module.py');
      expect(fileNames).not.toContain('another_fake.py');
    });

    it('should trace package submodules', async () => {
      const mainFile = join(fixturesDir, 'edge_cases', 'main.py');
      const result = await pythonFileTrace([mainFile], {
        base: join(fixturesDir, 'edge_cases'),
      });

      const filePaths = Array.from(result.fileList);
      const fileNames = filePaths.map((p) => p.split('/').pop());

      expect(fileNames).toContain('__init__.py');
      expect(fileNames).toContain('module_a.py');
      expect(fileNames).toContain('module_b.py');
    });
  });
});
