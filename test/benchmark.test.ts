/**
 * Performance benchmarks for python-file-trace.
 *
 * These benchmarks measure tracing performance against realistic Python codebases.
 * The FastAPI benchmark simulates a real-world application structure similar to
 * the Polar (polarsource/polar) codebase.
 *
 * Note: These tests are informational and should not fail CI. They are marked
 * with custom tags and can be run separately.
 */
import { describe, it, expect } from 'bun:test';
import { join } from 'node:path';
import { pythonFileTrace } from '../src/trace.js';

const fixturesDir = join(__dirname, 'fixtures');

/**
 * Measure execution time of an async function.
 */
async function measureTime<T>(
  fn: () => Promise<T>
): Promise<{ result: T; durationMs: number }> {
  const start = performance.now();
  const result = await fn();
  const durationMs = performance.now() - start;
  return { result, durationMs };
}

/**
 * Run a function multiple times and return timing statistics.
 */
async function benchmark<T>(
  fn: () => Promise<T>,
  iterations: number = 5
): Promise<{
  result: T;
  timings: number[];
  min: number;
  max: number;
  avg: number;
  median: number;
}> {
  const timings: number[] = [];
  let result: T | undefined;

  for (let i = 0; i < iterations; i++) {
    const { result: r, durationMs } = await measureTime(fn);
    result = r;
    timings.push(durationMs);
  }

  const sorted = [...timings].sort((a, b) => a - b);
  const min = sorted[0];
  const max = sorted[sorted.length - 1];
  const avg = timings.reduce((a, b) => a + b, 0) / timings.length;
  const median = sorted[Math.floor(sorted.length / 2)];

  return { result: result as T, timings, min, max, avg, median };
}

describe('benchmarks', () => {
  describe('FastAPI application benchmark', () => {
    /**
     * This benchmark traces a realistic FastAPI application structure
     * modeled after the Polar (polarsource/polar) codebase.
     *
     * Structure:
     * - app.py: Main application entry point
     * - core/: Configuration, security, logging
     * - db/: Database engine, sessions, base models
     * - middleware/: Auth, CORS, rate limiting, logging, errors
     * - api/: Routers and endpoint handlers
     * - services/: Business logic services
     * - models/: Database models
     * - schemas/: Request/response schemas
     * - tasks/: Background worker tasks
     */
    it('should trace FastAPI app within reasonable time', async () => {
      const mainFile = join(fixturesDir, 'benchmark_fastapi', 'app.py');

      const stats = await benchmark(
        () =>
          pythonFileTrace([mainFile], {
            base: join(fixturesDir, 'benchmark_fastapi'),
          }),
        5
      );

      const { result, min, max, avg, median } = stats;

      // Log benchmark results
      console.log('\n📊 FastAPI Benchmark Results:');
      console.log(`   Files traced: ${result.fileList.size}`);
      console.log(`   Unresolved:   ${result.unresolved.size}`);
      console.log(`   Warnings:     ${result.warnings.length}`);
      console.log(`   Timings (ms): min=${min.toFixed(2)}, max=${max.toFixed(2)}, avg=${avg.toFixed(2)}, median=${median.toFixed(2)}`);

      // Verify tracing works correctly
      const filePaths = Array.from(result.fileList);
      const fileNames = filePaths.map((p) => p.split('/').pop());

      // Should trace the main app
      expect(fileNames).toContain('app.py');

      // Should trace core modules
      expect(fileNames).toContain('config.py');
      expect(fileNames).toContain('security.py');
      expect(fileNames).toContain('logging.py');

      // Should trace database layer
      expect(fileNames).toContain('engine.py');
      expect(fileNames).toContain('session.py');
      expect(fileNames).toContain('base.py');

      // Should trace middleware
      expect(fileNames).toContain('auth.py');
      expect(fileNames).toContain('cors.py');
      expect(fileNames).toContain('ratelimit.py');

      // Should trace API endpoints
      expect(fileNames).toContain('health.py');
      expect(fileNames).toContain('users.py');
      expect(fileNames).toContain('organizations.py');
      expect(fileNames).toContain('subscriptions.py');
      expect(fileNames).toContain('webhooks.py');

      // Should trace services
      expect(fileNames).toContain('user_service.py');
      expect(fileNames).toContain('payment_service.py');
      expect(fileNames).toContain('email_service.py');

      // Should trace models
      expect(fileNames).toContain('user.py');
      expect(fileNames).toContain('organization.py');
      expect(fileNames).toContain('subscription.py');

      // Should trace schemas
      expect(fileNames).toContain('common.py');

      // Should trace at least 40 files (our realistic app)
      expect(result.fileList.size).toBeGreaterThanOrEqual(40);

      // Performance assertion (soft - logs warning but doesn't fail)
      // A reasonable threshold for tracing ~50 files
      const performanceThresholdMs = 5000; // 5 seconds max
      if (median > performanceThresholdMs) {
        console.warn(
          `⚠️  Performance warning: median time ${median.toFixed(2)}ms exceeds threshold of ${performanceThresholdMs}ms`
        );
      }
    });

    it('should benefit from caching on repeated traces', async () => {
      const mainFile = join(fixturesDir, 'benchmark_fastapi', 'app.py');
      const base = join(fixturesDir, 'benchmark_fastapi');

      const cache = {
        fileContents: new Map<string, string>(),
        parsedImports: new Map<string, unknown>(),
        resolvedModules: new Map<string, unknown>(),
        stdlibModules: new Set<string>(),
      };

      // First trace (cold cache)
      const { durationMs: coldDuration, result: coldResult } = await measureTime(
        () => pythonFileTrace([mainFile], { base, cache })
      );

      // Second trace (warm cache)
      const { durationMs: warmDuration, result: warmResult } = await measureTime(
        () => pythonFileTrace([mainFile], { base, cache })
      );

      console.log('\n🔥 Cache Performance:');
      console.log(`   Cold cache: ${coldDuration.toFixed(2)}ms`);
      console.log(`   Warm cache: ${warmDuration.toFixed(2)}ms`);
      console.log(
        `   Speedup:    ${(coldDuration / warmDuration).toFixed(2)}x`
      );
      console.log(`   Cache entries: fileContents=${cache.fileContents.size}, parsedImports=${cache.parsedImports.size}`);

      // Verify same results with cache
      expect(warmResult.fileList.size).toBe(coldResult.fileList.size);

      // Warm cache should generally be faster (but we don't fail on this)
      if (warmDuration >= coldDuration) {
        console.warn(
          '⚠️  Cache did not improve performance (this can happen on first runs)'
        );
      }
    });

    it('should handle concurrent file I/O efficiently', async () => {
      const mainFile = join(fixturesDir, 'benchmark_fastapi', 'app.py');
      const base = join(fixturesDir, 'benchmark_fastapi');

      // Test with different concurrency levels
      const concurrencyLevels = [1, 4, 8, 16];
      const results: { concurrency: number; durationMs: number; files: number }[] = [];

      for (const concurrency of concurrencyLevels) {
        const { durationMs, result } = await measureTime(() =>
          pythonFileTrace([mainFile], { base, concurrency })
        );
        results.push({
          concurrency,
          durationMs,
          files: result.fileList.size,
        });
      }

      console.log('\n🚀 Concurrency Performance:');
      for (const r of results) {
        console.log(
          `   concurrency=${r.concurrency}: ${r.durationMs.toFixed(2)}ms (${r.files} files)`
        );
      }

      // All concurrency levels should trace the same number of files
      const fileCounts = results.map((r) => r.files);
      expect(new Set(fileCounts).size).toBe(1);
    });
  });

  describe('memory efficiency', () => {
    it('should not leak memory on repeated traces', async () => {
      const mainFile = join(fixturesDir, 'benchmark_fastapi', 'app.py');
      const base = join(fixturesDir, 'benchmark_fastapi');

      // Force GC if available
      if (global.gc) {
        global.gc();
      }

      const initialHeap = process.memoryUsage().heapUsed;
      const iterations = 3; // Keep low to avoid timeout

      // Run multiple traces without shared cache
      for (let i = 0; i < iterations; i++) {
        await pythonFileTrace([mainFile], { base });
      }

      // Force GC if available
      if (global.gc) {
        global.gc();
      }

      const finalHeap = process.memoryUsage().heapUsed;
      const heapGrowthMB = (finalHeap - initialHeap) / 1024 / 1024;

      console.log('\n💾 Memory Usage:');
      console.log(`   Iterations:   ${iterations}`);
      console.log(`   Initial heap: ${(initialHeap / 1024 / 1024).toFixed(2)}MB`);
      console.log(`   Final heap:   ${(finalHeap / 1024 / 1024).toFixed(2)}MB`);
      console.log(`   Growth:       ${heapGrowthMB.toFixed(2)}MB`);

      // Warn if heap grew significantly (but don't fail)
      if (heapGrowthMB > 50) {
        console.warn(
          `⚠️  Heap grew by ${heapGrowthMB.toFixed(2)}MB after ${iterations} traces`
        );
      }
    });
  });
});
