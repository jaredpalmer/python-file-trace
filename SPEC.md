# Autotune: Blackbox AI Completion Scoring for RL Post-Training

## Overview

Autotune is a platform that enables third-party developers to contribute proprietary graders for AI model post-training via reinforcement learning (RL), without exposing their grading logic. This allows AI companies like Anthropic to leverage domain-specific expertise and private evaluation criteria while respecting intellectual property.

**Built for Vercel** - Autotune is designed to be deployed on Vercel, leveraging the [Workflow Development Kit (WDK)](https://github.com/vercel/workflow) for durable, long-running scoring operations that can pause, resume, and survive deployments.

### The Problem

AI companies want to improve their models using domain-specific feedback, but:
1. Domain experts don't want to share their proprietary evaluation logic
2. Training infrastructure can't easily integrate with external systems
3. There's no standard protocol for secure, blackbox scoring
4. Complex scoring pipelines need durability without infrastructure complexity

### The Solution

Autotune provides:
- A **Grader Protocol** that third parties implement as HTTP endpoints
- A **Task Registry** where scoring tasks are defined and managed
- A **Score Collector** that aggregates results for RL training pipelines
- **Privacy guarantees** ensuring grader logic remains opaque to the training system
- **Durable Workflows** powered by Vercel's Workflow SDK for async scoring operations

## Core Concepts

### Task
A definition of what needs to be scored, including the prompt template, expected behavior, and metadata.

```typescript
interface Task {
  id: string;
  name: string;
  description: string;
  promptTemplate: string;
  metadata: Record<string, unknown>;
  graderId: string;
  createdAt: Date;
  updatedAt: Date;
}
```

### Completion
A model's response to a task that needs to be scored.

```typescript
interface Completion {
  id: string;
  taskId: string;
  modelId: string;
  prompt: string;
  response: string;
  metadata: Record<string, unknown>;
  createdAt: Date;
}
```

### Score
The grader's evaluation of a completion.

```typescript
interface Score {
  id: string;
  completionId: string;
  graderId: string;
  value: number;           // Normalized score between 0 and 1
  confidence: number;      // Grader's confidence in the score (0-1)
  reasoning?: string;      // Optional explanation (can be redacted)
  dimensions?: ScoreDimension[];  // Multi-dimensional scoring
  createdAt: Date;
}

interface ScoreDimension {
  name: string;            // e.g., "correctness", "style", "safety"
  value: number;           // 0-1 normalized
  weight: number;          // Contribution to overall score
}
```

### Grader
A registered scoring endpoint that evaluates completions.

```typescript
interface Grader {
  id: string;
  name: string;
  description: string;
  endpoint: string;        // HTTPS URL
  owner: string;           // Organization ID
  capabilities: GraderCapabilities;
  authentication: AuthConfig;
  status: 'active' | 'inactive' | 'degraded';
  createdAt: Date;
  updatedAt: Date;
}

interface GraderCapabilities {
  maxBatchSize: number;
  supportsDimensions: boolean;
  supportsExplanations: boolean;
  supportsAsync: boolean;  // Supports long-running async scoring via workflows
  avgLatencyMs: number;
  domains: string[];       // e.g., ["code", "math", "legal"]
}
```

### Workflow Run
A durable execution context for async scoring operations.

```typescript
interface WorkflowRun {
  id: string;
  completionId: string;
  graderId: string;
  status: 'pending' | 'running' | 'sleeping' | 'waiting' | 'completed' | 'failed';
  currentStep?: string;
  startedAt: Date;
  completedAt?: Date;
  result?: Score;
  error?: string;
}
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           AI Training System                             │
│                    (e.g., Anthropic's RL Pipeline)                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Autotune Platform (Vercel)                            │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                     Vercel Workflow Engine                          │ │
│  │   • Durable execution for long-running scores                       │ │
│  │   • Automatic retry & state persistence                             │ │
│  │   • Sleep/pause without consuming compute                           │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │   Task      │  │  Workflow   │  │   Score     │  │    Grader       │ │
│  │  Registry   │  │  Orchestr.  │  │ Aggregator  │  │   Registry      │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                      Grader Gateway (Edge)                          │ │
│  │   • Request signing & verification                                  │ │
│  │   • Rate limiting & circuit breaking                                │ │
│  │   • Webhook handling for async responses                            │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                       Neon Postgres + Upstash Redis                 │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
    ┌───────────┐        ┌───────────┐        ┌───────────┐
    │  Grader A │        │  Grader B │        │  Grader C │
    │ (Next.js) │        │ (Vercel)  │        │ (External)│
    │ + Workflow│        │ Workflow  │        │   API     │
    └───────────┘        └───────────┘        └───────────┘
```

## Vercel Workflow SDK Integration

Autotune uses the [Vercel Workflow Development Kit](https://github.com/vercel/workflow) to enable durable, long-running scoring operations. This is particularly powerful for:

- **Complex scoring pipelines** that require multiple LLM calls
- **Human-in-the-loop** scoring that waits for manual review
- **Rate-limited APIs** where scoring must pause and resume
- **Multi-stage evaluation** with different scoring criteria

### Core Directives

The Workflow SDK introduces two directives that make async functions durable:

#### `"use workflow"` - Durable Function Declaration

Marks a function as a durable workflow that survives deployments and crashes:

```typescript
export async function scoreCompletion(completionId: string) {
  "use workflow";

  // This entire function is now durable
  // It can pause, resume, and maintain state
}
```

#### `"use step"` - Retriable Step Declaration

Marks individual operations as isolated, retriable steps:

```typescript
async function analyzeCode(code: string) {
  "use step";

  // This step executes independently with automatic retry
  // Results are persisted - if the workflow restarts, this won't re-run
  return await llm.analyze(code);
}
```

### Workflow-Based Scoring Example

```typescript
// app/api/score/[completionId]/route.ts
import { sleep, createWebhook } from '@vercel/workflow';

export async function POST(req: Request, { params }: { params: { completionId: string } }) {
  "use workflow";

  const { completionId } = params;

  // Step 1: Fetch the completion (retriable)
  const completion = await fetchCompletion(completionId);

  // Step 2: Run syntax analysis
  const syntaxScore = await analyzeSyntax(completion.response);

  // Step 3: Run semantic analysis (may take a while)
  const semanticScore = await analyzeSemantics(completion.response);

  // Step 4: If confidence is low, wait for human review
  if (semanticScore.confidence < 0.7) {
    const webhook = createWebhook<{ approved: boolean; adjustedScore?: number }>();

    await notifyReviewer({
      completionId,
      preliminaryScore: semanticScore.value,
      reviewUrl: webhook.url,
    });

    // Workflow pauses here - no compute consumed
    // Resumes when webhook is called (could be hours/days later)
    const { request } = await webhook;
    const review = await request.json();

    if (review.adjustedScore !== undefined) {
      semanticScore.value = review.adjustedScore;
      semanticScore.confidence = 1.0;
    }
  }

  // Step 5: Aggregate and save final score
  const finalScore = await aggregateScores([syntaxScore, semanticScore]);
  await saveScore(completionId, finalScore);

  return Response.json({ score: finalScore });
}

async function fetchCompletion(id: string) {
  "use step";
  const res = await fetch(`${process.env.API_URL}/completions/${id}`);
  return res.json();
}

async function analyzeSyntax(code: string) {
  "use step";
  // Your proprietary syntax analysis
  return { value: 0.85, confidence: 0.95, dimension: 'syntax' };
}

async function analyzeSemantics(code: string) {
  "use step";
  // Complex semantic analysis - might call external LLMs
  const result = await llm.analyze(code);
  return { value: result.score, confidence: result.confidence, dimension: 'semantics' };
}

async function aggregateScores(scores: Array<{ value: number; confidence: number }>) {
  "use step";
  const weightedSum = scores.reduce((acc, s) => acc + s.value * s.confidence, 0);
  const totalWeight = scores.reduce((acc, s) => acc + s.confidence, 0);
  return { value: weightedSum / totalWeight, confidence: Math.min(...scores.map(s => s.confidence)) };
}
```

### Sleep for Delayed Scoring

Workflows can pause for extended periods without consuming resources:

```typescript
export async function batchScoreWithRateLimit(completionIds: string[]) {
  "use workflow";

  const scores = [];

  for (const id of completionIds) {
    const score = await scoreOne(id);
    scores.push(score);

    // Sleep to respect rate limits - workflow pauses entirely
    await sleep("500ms");
  }

  // For longer delays (e.g., waiting for daily batch)
  await sleep("6h");

  return scores;
}
```

### Webhook-Based Async Grading

For graders that need human review or external async processes:

```typescript
export async function scoreWithExternalReview(completionId: string) {
  "use workflow";

  const completion = await fetchCompletion(completionId);

  // Create a webhook that the external system will call
  const webhook = createWebhook<ScoreResponse>();

  // Send to external grading system
  await fetch(process.env.EXTERNAL_GRADER_URL, {
    method: 'POST',
    body: JSON.stringify({
      completion,
      callbackUrl: webhook.url,  // They'll POST the score here
    }),
  });

  // Workflow suspends - could be minutes, hours, or days
  // No compute consumed while waiting
  const { request } = await webhook;
  const externalScore = await request.json();

  // Continue processing with the score
  await saveScore(completionId, externalScore);

  return externalScore;
}
```

## Grader Protocol

### HTTP Interface

Graders must implement the following HTTP endpoints:

#### `POST /score`

Score a single completion.

**Request:**
```typescript
interface ScoreRequest {
  requestId: string;
  completion: {
    id: string;
    taskId: string;
    prompt: string;
    response: string;
    metadata?: Record<string, unknown>;
  };
  options?: {
    includeDimensions?: boolean;
    includeExplanation?: boolean;
  };
}
```

**Response:**
```typescript
interface ScoreResponse {
  requestId: string;
  score: {
    value: number;           // 0-1
    confidence: number;      // 0-1
    dimensions?: ScoreDimension[];
    reasoning?: string;
  };
  processingTimeMs: number;
}
```

#### `POST /score/batch`

Score multiple completions in a single request.

**Request:**
```typescript
interface BatchScoreRequest {
  requestId: string;
  completions: Array<{
    id: string;
    taskId: string;
    prompt: string;
    response: string;
    metadata?: Record<string, unknown>;
  }>;
  options?: {
    includeDimensions?: boolean;
    includeExplanation?: boolean;
  };
}
```

**Response:**
```typescript
interface BatchScoreResponse {
  requestId: string;
  scores: Array<{
    completionId: string;
    score: {
      value: number;
      confidence: number;
      dimensions?: ScoreDimension[];
      reasoning?: string;
    };
    error?: string;
  }>;
  processingTimeMs: number;
}
```

#### `GET /health`

Health check endpoint.

**Response:**
```typescript
interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  capabilities: GraderCapabilities;
}
```

### Authentication

Graders authenticate requests using HMAC-SHA256 signatures:

```typescript
// Request headers
{
  'X-Autotune-Signature': string;     // HMAC signature
  'X-Autotune-Timestamp': string;     // Unix timestamp
  'X-Autotune-Request-Id': string;    // Unique request ID
}

// Signature computation
const payload = `${timestamp}.${requestId}.${JSON.stringify(body)}`;
const signature = hmacSha256(payload, sharedSecret);
```

### Response Signing

Graders sign responses to ensure integrity:

```typescript
// Response headers
{
  'X-Autotune-Response-Signature': string;
  'X-Autotune-Response-Timestamp': string;
}
```

## Autotune API

### Task Management

#### `POST /api/v1/tasks`

Create a new scoring task.

```typescript
// Request
interface CreateTaskRequest {
  name: string;
  description: string;
  promptTemplate: string;
  graderId: string;
  metadata?: Record<string, unknown>;
}

// Response
interface CreateTaskResponse {
  task: Task;
}
```

#### `GET /api/v1/tasks`

List all tasks.

#### `GET /api/v1/tasks/:id`

Get a specific task.

### Completion Submission

#### `POST /api/v1/completions`

Submit a completion for scoring.

```typescript
// Request
interface SubmitCompletionRequest {
  taskId: string;
  modelId: string;
  prompt: string;
  response: string;
  metadata?: Record<string, unknown>;
  priority?: 'low' | 'normal' | 'high';
}

// Response
interface SubmitCompletionResponse {
  completion: Completion;
  estimatedScoreTimeMs: number;
}
```

#### `POST /api/v1/completions/batch`

Submit multiple completions.

```typescript
// Request
interface BatchSubmitRequest {
  completions: Array<{
    taskId: string;
    modelId: string;
    prompt: string;
    response: string;
    metadata?: Record<string, unknown>;
  }>;
  priority?: 'low' | 'normal' | 'high';
}
```

### Score Retrieval

#### `GET /api/v1/completions/:id/score`

Get the score for a completion.

```typescript
// Response
interface GetScoreResponse {
  score: Score | null;
  status: 'pending' | 'processing' | 'completed' | 'failed';
}
```

#### `GET /api/v1/scores`

Query scores with filters.

```typescript
// Query parameters
interface ScoreQuery {
  taskId?: string;
  modelId?: string;
  minScore?: number;
  maxScore?: number;
  startDate?: string;
  endDate?: string;
  limit?: number;
  offset?: number;
}
```

#### `GET /api/v1/scores/export`

Export scores in RL-training-ready format.

```typescript
// Query parameters
interface ExportQuery {
  taskId?: string;
  modelId?: string;
  format: 'jsonl' | 'parquet' | 'tfrecord';
  startDate?: string;
  endDate?: string;
}

// JSONL output format (one per line)
interface RLTrainingRecord {
  prompt: string;
  response: string;
  score: number;
  dimensions?: Record<string, number>;
  metadata: {
    taskId: string;
    modelId: string;
    completionId: string;
    graderId: string;
    confidence: number;
  };
}
```

### Grader Management

#### `POST /api/v1/graders`

Register a new grader.

```typescript
// Request
interface RegisterGraderRequest {
  name: string;
  description: string;
  endpoint: string;
  capabilities: GraderCapabilities;
}

// Response includes the shared secret for authentication
interface RegisterGraderResponse {
  grader: Grader;
  credentials: {
    graderId: string;
    sharedSecret: string;  // Only returned once!
  };
}
```

#### `POST /api/v1/graders/:id/verify`

Verify a grader's endpoint is correctly configured.

#### `GET /api/v1/graders/:id/stats`

Get grader performance statistics.

```typescript
interface GraderStats {
  totalScored: number;
  avgLatencyMs: number;
  p99LatencyMs: number;
  errorRate: number;
  avgScore: number;
  scoreDistribution: number[];  // Histogram buckets
}
```

## Webhooks

### Score Completed

Notify when a score is ready.

```typescript
interface ScoreCompletedWebhook {
  event: 'score.completed';
  data: {
    completionId: string;
    score: Score;
  };
  timestamp: string;
}
```

### Grader Status Change

Notify when a grader's status changes.

```typescript
interface GraderStatusWebhook {
  event: 'grader.status_changed';
  data: {
    graderId: string;
    previousStatus: string;
    currentStatus: string;
    reason?: string;
  };
  timestamp: string;
}
```

## Security Model

### Blackbox Guarantees

1. **Grader Logic Privacy**: Autotune never sees or stores grader implementation details
2. **Score Integrity**: Signed responses prevent tampering
3. **Request Authentication**: Only authorized requests reach graders
4. **Transport Security**: All communication over HTTPS with certificate pinning

### Data Handling

1. **Prompt/Response Storage**: Configurable retention policies
2. **Score Storage**: Permanent by default, exportable
3. **Audit Logging**: All API calls logged with requestor identity
4. **Encryption**: Data encrypted at rest using AES-256

### Access Control

```typescript
interface Permission {
  resource: 'tasks' | 'completions' | 'scores' | 'graders';
  actions: ('create' | 'read' | 'update' | 'delete')[];
  scope: 'own' | 'organization' | 'all';
}

interface Role {
  name: string;
  permissions: Permission[];
}

// Built-in roles
const ROLES = {
  grader_owner: {
    permissions: [
      { resource: 'graders', actions: ['create', 'read', 'update', 'delete'], scope: 'own' },
      { resource: 'scores', actions: ['read'], scope: 'own' },
    ]
  },
  training_operator: {
    permissions: [
      { resource: 'tasks', actions: ['create', 'read', 'update'], scope: 'organization' },
      { resource: 'completions', actions: ['create', 'read'], scope: 'organization' },
      { resource: 'scores', actions: ['read'], scope: 'organization' },
    ]
  },
  admin: {
    permissions: [
      { resource: 'tasks', actions: ['create', 'read', 'update', 'delete'], scope: 'all' },
      { resource: 'completions', actions: ['create', 'read', 'delete'], scope: 'all' },
      { resource: 'scores', actions: ['read', 'delete'], scope: 'all' },
      { resource: 'graders', actions: ['create', 'read', 'update', 'delete'], scope: 'all' },
    ]
  }
};
```

## TypeScript SDK

### Client Usage

```typescript
import { AutotuneClient } from '@autotune/sdk';

const client = new AutotuneClient({
  apiKey: process.env.AUTOTUNE_API_KEY,
  baseUrl: 'https://api.autotune.ai',
});

// Submit a completion for scoring
const { completion } = await client.completions.submit({
  taskId: 'task_abc123',
  modelId: 'claude-3-opus',
  prompt: 'Write a function to calculate fibonacci numbers',
  response: 'def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)',
});

// Wait for and retrieve the score
const { score } = await client.completions.waitForScore(completion.id, {
  timeoutMs: 30000,
});

console.log(`Score: ${score.value}, Confidence: ${score.confidence}`);
```

### Grader SDK

The Grader SDK supports both simple synchronous graders and complex async graders using Vercel Workflows.

#### Simple Grader (App Router)

```typescript
import { createGrader, GraderContext } from '@autotune/grader-sdk';

// Define your grader
const grader = createGrader({
  name: 'code-quality-grader',
  version: '1.0.0',

  async score(ctx: GraderContext) {
    const { prompt, response } = ctx.completion;

    // Your proprietary scoring logic here
    const analysis = await analyzeCode(response);

    return {
      value: analysis.overallScore,
      confidence: 0.95,
      dimensions: [
        { name: 'correctness', value: analysis.correctness, weight: 0.5 },
        { name: 'efficiency', value: analysis.efficiency, weight: 0.3 },
        { name: 'readability', value: analysis.readability, weight: 0.2 },
      ],
    };
  },
});

// Next.js App Router handler
export const POST = grader.handler();
```

#### Workflow-Based Grader (Long-Running/Async)

For graders that need to perform complex, multi-step scoring:

```typescript
// app/api/score/route.ts
import { createWorkflowGrader } from '@autotune/grader-sdk';
import { sleep, createWebhook } from '@vercel/workflow';

export const POST = createWorkflowGrader({
  name: 'multi-stage-grader',
  version: '1.0.0',

  async score(ctx) {
    "use workflow";

    const { prompt, response } = ctx.completion;

    // Step 1: Quick syntax check
    const syntaxScore = await checkSyntax(response);

    // Step 2: Deep semantic analysis (may take a while)
    const semanticScore = await analyzeSemantics(response);

    // Step 3: Run against test suite
    const testScore = await runTests(response);

    // Aggregate scores
    return {
      value: (syntaxScore.value * 0.2 + semanticScore.value * 0.5 + testScore.value * 0.3),
      confidence: Math.min(syntaxScore.confidence, semanticScore.confidence, testScore.confidence),
      dimensions: [
        { name: 'syntax', value: syntaxScore.value, weight: 0.2 },
        { name: 'semantics', value: semanticScore.value, weight: 0.5 },
        { name: 'tests', value: testScore.value, weight: 0.3 },
      ],
    };
  },
});

async function checkSyntax(code: string) {
  "use step";
  // Fast syntax validation
  return { value: 0.9, confidence: 0.99 };
}

async function analyzeSemantics(code: string) {
  "use step";
  // Call LLM for semantic analysis
  const result = await llm.analyze(code);
  return { value: result.score, confidence: result.confidence };
}

async function runTests(code: string) {
  "use step";
  // Execute in sandbox
  const result = await sandbox.run(code);
  return { value: result.passRate, confidence: 1.0 };
}
```

#### Human-in-the-Loop Grader

For graders that require manual review:

```typescript
// app/api/score/route.ts
import { createWorkflowGrader } from '@autotune/grader-sdk';
import { createWebhook } from '@vercel/workflow';

export const POST = createWorkflowGrader({
  name: 'human-review-grader',
  version: '1.0.0',

  async score(ctx) {
    "use workflow";

    const { prompt, response } = ctx.completion;

    // Step 1: AI preliminary score
    const aiScore = await getAIScore(response);

    // Step 2: If AI confidence is low, request human review
    if (aiScore.confidence < 0.8) {
      const webhook = createWebhook<{ score: number; feedback: string }>();

      // Create review request in database
      await createReviewRequest({
        completionId: ctx.completion.id,
        aiScore,
        callbackUrl: webhook.url,
      });

      // Send notification to reviewers
      await notifyReviewers(ctx.completion.id);

      // Workflow pauses here until human submits review
      // No compute consumed while waiting
      const { request } = await webhook;
      const humanReview = await request.json();

      return {
        value: humanReview.score,
        confidence: 1.0,  // Human review = full confidence
        reasoning: humanReview.feedback,
        dimensions: [
          { name: 'ai_preliminary', value: aiScore.value, weight: 0 },
          { name: 'human_review', value: humanReview.score, weight: 1.0 },
        ],
      };
    }

    return aiScore;
  },
});
```

## Example: Next.js Grader Implementation

```typescript
// pages/api/grader/score.ts
import { NextApiRequest, NextApiResponse } from 'next';
import { verifyRequest, signResponse, ScoreRequest, ScoreResponse } from '@autotune/grader-sdk';

const SHARED_SECRET = process.env.AUTOTUNE_GRADER_SECRET!;

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Verify the request signature
  if (!verifyRequest(req, SHARED_SECRET)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  const scoreRequest: ScoreRequest = req.body;
  const startTime = Date.now();

  try {
    // Your proprietary grading logic
    const score = await gradeCompletion(scoreRequest.completion);

    const response: ScoreResponse = {
      requestId: scoreRequest.requestId,
      score: {
        value: score.value,
        confidence: score.confidence,
        dimensions: score.dimensions,
        reasoning: score.reasoning,
      },
      processingTimeMs: Date.now() - startTime,
    };

    // Sign the response
    const signedHeaders = signResponse(response, SHARED_SECRET);
    Object.entries(signedHeaders).forEach(([key, value]) => {
      res.setHeader(key, value);
    });

    return res.status(200).json(response);
  } catch (error) {
    return res.status(500).json({
      requestId: scoreRequest.requestId,
      error: 'Scoring failed',
    });
  }
}

async function gradeCompletion(completion: { prompt: string; response: string }) {
  // Example: Grade code quality using AST analysis
  // This logic stays private - Autotune only sees the score

  const ast = parseCode(completion.response);
  const metrics = analyzeAST(ast);

  return {
    value: calculateScore(metrics),
    confidence: 0.92,
    dimensions: [
      { name: 'syntax', value: metrics.syntaxScore, weight: 0.3 },
      { name: 'semantics', value: metrics.semanticsScore, weight: 0.4 },
      { name: 'style', value: metrics.styleScore, weight: 0.3 },
    ],
    reasoning: `Analyzed ${metrics.nodeCount} AST nodes`,
  };
}
```

## RL Training Integration

### Export Format for Training

```typescript
// Export scores in format compatible with RL training pipelines
interface RLTrainingDataset {
  metadata: {
    exportedAt: string;
    taskIds: string[];
    modelIds: string[];
    totalRecords: number;
    scoreDistribution: {
      mean: number;
      std: number;
      min: number;
      max: number;
      percentiles: { p25: number; p50: number; p75: number; p95: number };
    };
  };
  records: RLTrainingRecord[];
}

// Compatible with common RLHF frameworks
interface RLTrainingRecord {
  // Core fields for training
  prompt: string;
  chosen?: string;      // High-scoring response (for preference learning)
  rejected?: string;    // Low-scoring response (for preference learning)
  response?: string;    // Single response (for reward modeling)
  score?: number;       // Numerical score (for reward modeling)

  // Metadata for filtering/analysis
  metadata: {
    task_id: string;
    model_id: string;
    grader_id: string;
    confidence: number;
    dimensions?: Record<string, number>;
  };
}
```

### Preference Pair Generation

```typescript
// Generate preference pairs from scores for DPO/RLHF training
interface PreferencePairRequest {
  taskId: string;
  modelId: string;
  minScoreDelta: number;  // Minimum difference between chosen/rejected
  sampleSize: number;
}

interface PreferencePair {
  prompt: string;
  chosen: string;
  rejected: string;
  chosenScore: number;
  rejectedScore: number;
}
```

## Deployment Architecture

### Vercel Deployment

Autotune is designed as a Vercel-native application, leveraging:

- **Vercel Functions** - API routes for all endpoints
- **Vercel Workflow** - Durable execution for async scoring
- **[Neon](https://neon.tech)** - Serverless Postgres database
- **[Upstash Redis](https://upstash.com)** - Caching and rate limiting (serverless Redis)
- **Vercel Edge Config** - Feature flags and grader configuration
- **Vercel Blob** - Large response storage and exports

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Vercel Edge Network                             │
│                        (Global CDN, DDoS Protection)                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
            ▼                         ▼                         ▼
   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
   │  Edge Middleware│     │ API Routes      │     │ Workflow Engine │
   │  • Auth/HMAC    │     │ /api/v1/*       │     │ "use workflow"  │
   │  • Rate Limit   │     │ Next.js App     │     │ "use step"      │
   │  • Routing      │     │ Router          │     │ Durable Fns     │
   └────────┬────────┘     └────────┬────────┘     └────────┬────────┘
            │                       │                       │
            └───────────────────────┼───────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
         ▼                          ▼                          ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Neon Postgres  │      │  Upstash Redis  │      │  Vercel Blob    │
│ • Tasks         │      │ • Rate limits   │      │ • Score exports │
│ • Completions   │      │ • Session cache │      │ • Large payloads│
│ • Scores        │      │ • Grader status │      │ • Audit logs    │
│ • Graders       │      │                 │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

### Environment Configuration

```bash
# .env.local
# Neon Postgres
DATABASE_URL="postgres://...@...neon.tech/..."

# Upstash Redis
UPSTASH_REDIS_REST_URL="https://..."
UPSTASH_REDIS_REST_TOKEN="..."

# Vercel Services
BLOB_READ_WRITE_TOKEN="..."

# Autotune Configuration
AUTOTUNE_SIGNING_SECRET="..."
AUTOTUNE_WEBHOOK_SECRET="..."

# Workflow Configuration
WORKFLOW_SECRET="..."
```

### vercel.json Configuration

```json
{
  "framework": "nextjs",
  "functions": {
    "app/api/v1/completions/*/score/route.ts": {
      "maxDuration": 300
    },
    "app/api/v1/scores/export/route.ts": {
      "maxDuration": 300
    }
  },
  "crons": [
    {
      "path": "/api/cron/cleanup-expired-workflows",
      "schedule": "0 0 * * *"
    },
    {
      "path": "/api/cron/grader-health-check",
      "schedule": "*/5 * * * *"
    }
  ]
}
```

### Workflow-Based Scoring Flow

```typescript
// app/api/v1/completions/route.ts
import { redirect } from 'next/navigation';

export async function POST(req: Request) {
  const body = await req.json();

  // Save completion to database
  const completion = await db.completions.create({
    data: {
      taskId: body.taskId,
      modelId: body.modelId,
      prompt: body.prompt,
      response: body.response,
      metadata: body.metadata,
    },
  });

  // Trigger the scoring workflow (runs async/durably)
  const workflowRun = await triggerScoringWorkflow(completion.id);

  return Response.json({
    completion,
    workflowRunId: workflowRun.id,
    status: 'scoring',
  });
}

// app/api/workflows/score/[completionId]/route.ts
import { sleep, createWebhook } from '@vercel/workflow';

export async function POST(req: Request, { params }: { params: { completionId: string } }) {
  "use workflow";

  const completion = await fetchCompletion(params.completionId);
  const grader = await fetchGrader(completion.task.graderId);

  // Call the grader (with automatic retry on failure)
  const score = await callGrader(grader, completion);

  // Save the score
  await saveScore(completion.id, score);

  // Notify via webhook
  await emitWebhook('score.completed', {
    completionId: completion.id,
    score,
  });

  return Response.json({ success: true, score });
}

async function callGrader(grader: Grader, completion: Completion) {
  "use step";

  const response = await fetch(grader.endpoint, {
    method: 'POST',
    headers: signRequest(grader),
    body: JSON.stringify({
      requestId: crypto.randomUUID(),
      completion: {
        id: completion.id,
        taskId: completion.taskId,
        prompt: completion.prompt,
        response: completion.response,
      },
    }),
  });

  if (!response.ok) {
    throw new Error(`Grader returned ${response.status}`);
  }

  return response.json();
}
```

### One-Click Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/your-org/autotune)

```bash
# Or deploy via CLI
npx vercel --prod
```

## Project Structure

```
autotune/
├── app/                          # Next.js App Router
│   ├── api/
│   │   ├── v1/
│   │   │   ├── tasks/
│   │   │   │   ├── route.ts              # GET, POST /api/v1/tasks
│   │   │   │   └── [id]/route.ts         # GET, PATCH, DELETE /api/v1/tasks/:id
│   │   │   ├── completions/
│   │   │   │   ├── route.ts              # POST /api/v1/completions
│   │   │   │   ├── batch/route.ts        # POST /api/v1/completions/batch
│   │   │   │   └── [id]/
│   │   │   │       ├── route.ts          # GET /api/v1/completions/:id
│   │   │   │       └── score/route.ts    # GET /api/v1/completions/:id/score
│   │   │   ├── scores/
│   │   │   │   ├── route.ts              # GET /api/v1/scores
│   │   │   │   └── export/route.ts       # GET /api/v1/scores/export
│   │   │   ├── graders/
│   │   │   │   ├── route.ts              # GET, POST /api/v1/graders
│   │   │   │   └── [id]/
│   │   │   │       ├── route.ts          # GET, PATCH, DELETE
│   │   │   │       ├── verify/route.ts   # POST /api/v1/graders/:id/verify
│   │   │   │       └── stats/route.ts    # GET /api/v1/graders/:id/stats
│   │   │   └── webhooks/
│   │   │       └── route.ts              # Webhook management
│   │   ├── workflows/                    # Workflow endpoints
│   │   │   └── score/
│   │   │       └── [completionId]/route.ts  # Durable scoring workflow
│   │   └── cron/
│   │       ├── cleanup-expired-workflows/route.ts
│   │       └── grader-health-check/route.ts
│   ├── dashboard/                # Optional admin dashboard
│   │   ├── page.tsx
│   │   ├── graders/page.tsx
│   │   ├── tasks/page.tsx
│   │   └── scores/page.tsx
│   ├── layout.tsx
│   └── page.tsx
│
├── lib/
│   ├── db/
│   │   ├── schema.ts             # Drizzle ORM schema
│   │   ├── client.ts             # Database client
│   │   └── migrations/           # Database migrations
│   ├── auth/
│   │   ├── signing.ts            # HMAC request/response signing
│   │   └── verify.ts             # Signature verification
│   ├── graders/
│   │   ├── gateway.ts            # Grader proxy/gateway
│   │   ├── health.ts             # Health check utilities
│   │   └── registry.ts           # Grader registration
│   ├── workflows/
│   │   ├── scoring.ts            # Scoring workflow logic
│   │   └── hooks.ts              # Webhook utilities
│   └── utils/
│       ├── validation.ts         # Zod schemas
│       └── rate-limit.ts         # Rate limiting with Upstash Redis
│
├── packages/
│   ├── sdk/                      # @autotune/sdk - Client SDK
│   │   ├── src/
│   │   │   ├── index.ts
│   │   │   ├── client.ts
│   │   │   ├── resources/
│   │   │   │   ├── tasks.ts
│   │   │   │   ├── completions.ts
│   │   │   │   ├── scores.ts
│   │   │   │   └── graders.ts
│   │   │   └── types.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── grader-sdk/               # @autotune/grader-sdk - Grader SDK
│       ├── src/
│       │   ├── index.ts
│       │   ├── grader.ts         # createGrader factory
│       │   ├── workflow.ts       # Workflow-based grader helpers
│       │   ├── middleware.ts     # Next.js/Express middleware
│       │   ├── verification.ts   # Request verification
│       │   └── types.ts
│       ├── package.json
│       └── tsconfig.json
│
├── examples/
│   ├── grader-simple/            # Simple synchronous grader
│   │   ├── app/api/score/route.ts
│   │   └── package.json
│   ├── grader-workflow/          # Async grader with workflows
│   │   ├── app/api/score/route.ts
│   │   └── package.json
│   ├── grader-human-review/      # Human-in-the-loop grader
│   │   ├── app/
│   │   │   ├── api/score/route.ts
│   │   │   └── review/[id]/page.tsx
│   │   └── package.json
│   └── training-export/          # RL training data export
│       └── export.ts
│
├── middleware.ts                 # Edge middleware (auth, rate limiting)
├── vercel.json                   # Vercel configuration
├── drizzle.config.ts             # Drizzle ORM config
├── next.config.js                # Next.js configuration
├── package.json
├── pnpm-workspace.yaml           # Monorepo workspace config
├── turbo.json                    # Turborepo config
├── tsconfig.json
├── .env.example
├── SPEC.md
└── README.md
```

## Milestones

### Phase 1: Core Platform
- [ ] Core types and Zod validation schemas
- [ ] Drizzle ORM schema and Neon Postgres setup
- [ ] Basic API routes with task/completion/score CRUD
- [ ] Simple grader protocol implementation
- [ ] HMAC request/response signing
- [ ] Deploy to Vercel

### Phase 2: Workflow Integration
- [ ] Vercel Workflow SDK setup
- [ ] Durable scoring workflow implementation
- [ ] Step-based grader calls with automatic retry
- [ ] Sleep/pause support for rate-limited graders
- [ ] Webhook-based async completion notifications

### Phase 3: Grader Gateway
- [ ] Grader registration and verification
- [ ] Edge middleware for auth and rate limiting
- [ ] Circuit breaking for unhealthy graders
- [ ] Health monitoring with Vercel crons
- [ ] Grader status dashboard

### Phase 4: SDKs
- [ ] @autotune/sdk - Client SDK for training pipelines
- [ ] @autotune/grader-sdk - Simple grader helpers
- [ ] Workflow-based grader utilities
- [ ] Human-in-the-loop grader example
- [ ] Documentation and examples

### Phase 5: RL Integration
- [ ] Score export to Vercel Blob (JSONL, Parquet)
- [ ] Preference pair generation API
- [ ] Integration guides for common RL frameworks
- [ ] Streaming export for large datasets

### Phase 6: Scale & Polish
- [ ] Edge caching for frequently accessed scores
- [ ] Advanced analytics dashboard
- [ ] Grader marketplace
- [ ] Observability with Vercel's workflow monitoring
- [ ] Audit logging and compliance features

## Success Metrics

1. **Latency**: p99 scoring latency < 5 seconds
2. **Throughput**: 10,000+ completions scored per minute
3. **Reliability**: 99.9% uptime for platform, graceful degradation for graders
4. **Adoption**: 100+ registered graders within 6 months
5. **Data Quality**: < 1% scoring failures due to platform issues

## Open Questions

1. **Grader Compensation**: How should grader owners be compensated for scoring?
2. **Quality Assurance**: How do we validate grader quality without seeing the logic?
3. **Versioning**: How do we handle grader updates that change scoring behavior?
4. **Multi-grader Consensus**: Should we support scoring by multiple graders with aggregation?
5. **Feedback Loops**: Can we expose aggregate feedback to graders for improvement?

---

*This specification is a living document and will be updated as the project evolves.*
