# Autotune: Blackbox AI Completion Scoring for RL Post-Training

## Overview

Autotune is a platform that enables third-party developers to contribute proprietary graders for AI model post-training via reinforcement learning (RL), without exposing their grading logic. This allows AI companies like Anthropic to leverage domain-specific expertise and private evaluation criteria while respecting intellectual property.

### The Problem

AI companies want to improve their models using domain-specific feedback, but:
1. Domain experts don't want to share their proprietary evaluation logic
2. Training infrastructure can't easily integrate with external systems
3. There's no standard protocol for secure, blackbox scoring

### The Solution

Autotune provides:
- A **Grader Protocol** that third parties implement as HTTP endpoints
- A **Task Registry** where scoring tasks are defined and managed
- A **Score Collector** that aggregates results for RL training pipelines
- **Privacy guarantees** ensuring grader logic remains opaque to the training system

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
  avgLatencyMs: number;
  domains: string[];       // e.g., ["code", "math", "legal"]
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
│                           Autotune Platform                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │   Task      │  │ Completion  │  │   Score     │  │    Grader       │ │
│  │  Registry   │  │   Queue     │  │ Aggregator  │  │   Registry      │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                      Grader Gateway (Proxy)                         │ │
│  │   • Request signing & verification                                  │ │
│  │   • Rate limiting & circuit breaking                                │ │
│  │   • Response validation                                             │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
    ┌───────────┐        ┌───────────┐        ┌───────────┐
    │  Grader A │        │  Grader B │        │  Grader C │
    │ (Next.js) │        │  (Python) │        │   (Rust)  │
    │  Private  │        │  Private  │        │  Private  │
    └───────────┘        └───────────┘        └───────────┘
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

```typescript
import { createGrader, GraderContext } from '@autotune/grader-sdk';
import { NextApiRequest, NextApiResponse } from 'next';

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

// Next.js API route handler
export default function handler(req: NextApiRequest, res: NextApiResponse) {
  return grader.handle(req, res);
}
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

### Production Setup

```
                                    ┌─────────────────┐
                                    │   CloudFlare    │
                                    │   (DDoS/WAF)    │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │  Load Balancer  │
                                    │    (nginx)      │
                                    └────────┬────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
           ┌────────▼────────┐     ┌────────▼────────┐     ┌────────▼────────┐
           │   API Server    │     │   API Server    │     │   API Server    │
           │   (Node.js)     │     │   (Node.js)     │     │   (Node.js)     │
           └────────┬────────┘     └────────┬────────┘     └────────┬────────┘
                    │                        │                        │
                    └────────────────────────┼────────────────────────┘
                                             │
              ┌──────────────────────────────┼──────────────────────────────┐
              │                              │                              │
     ┌────────▼────────┐           ┌────────▼────────┐           ┌────────▼────────┐
     │   PostgreSQL    │           │     Redis       │           │    Bull MQ      │
     │   (Primary)     │           │    (Cache)      │           │    (Queue)      │
     └─────────────────┘           └─────────────────┘           └─────────────────┘
```

### Queue-Based Scoring Flow

```typescript
// Completion submission adds to queue
await completionQueue.add('score', {
  completionId: completion.id,
  graderId: task.graderId,
  priority: request.priority,
}, {
  attempts: 3,
  backoff: { type: 'exponential', delay: 1000 },
});

// Worker processes scoring requests
completionQueue.process('score', async (job) => {
  const { completionId, graderId } = job.data;

  const completion = await getCompletion(completionId);
  const grader = await getGrader(graderId);

  const score = await callGrader(grader, completion);
  await saveScore(score);

  // Emit webhook
  await webhookQueue.add('emit', {
    event: 'score.completed',
    data: { completionId, score },
  });
});
```

## Project Structure

```
autotune/
├── packages/
│   ├── core/                    # Shared types and utilities
│   │   ├── src/
│   │   │   ├── types/           # TypeScript interfaces
│   │   │   ├── validation/      # Zod schemas
│   │   │   └── crypto/          # Signing utilities
│   │   └── package.json
│   │
│   ├── server/                  # Main API server
│   │   ├── src/
│   │   │   ├── api/             # Route handlers
│   │   │   ├── services/        # Business logic
│   │   │   ├── queue/           # Job processing
│   │   │   ├── db/              # Database access
│   │   │   └── gateway/         # Grader proxy
│   │   └── package.json
│   │
│   ├── sdk/                     # Client SDK
│   │   ├── src/
│   │   │   ├── client.ts
│   │   │   ├── resources/
│   │   │   └── types.ts
│   │   └── package.json
│   │
│   └── grader-sdk/              # Grader implementation SDK
│       ├── src/
│       │   ├── grader.ts
│       │   ├── middleware.ts
│       │   ├── verification.ts
│       │   └── handlers/
│       └── package.json
│
├── examples/
│   ├── nextjs-grader/           # Example Next.js grader
│   ├── express-grader/          # Example Express grader
│   └── training-export/         # Example RL training integration
│
├── docker/
│   ├── Dockerfile.server
│   └── docker-compose.yml
│
├── docs/
│   ├── getting-started.md
│   ├── grader-guide.md
│   └── api-reference.md
│
├── SPEC.md
├── package.json
├── turbo.json
└── tsconfig.json
```

## Milestones

### Phase 1: Core Platform
- [ ] Core types and validation schemas
- [ ] Database schema and migrations
- [ ] Basic API server with task/completion/score CRUD
- [ ] Simple grader protocol implementation
- [ ] Request/response signing

### Phase 2: Grader Gateway
- [ ] Grader registration and verification
- [ ] Secure proxy with circuit breaking
- [ ] Batch scoring support
- [ ] Health monitoring and alerting

### Phase 3: SDKs
- [ ] Client SDK for training pipelines
- [ ] Grader SDK for Next.js
- [ ] Grader SDK for Express
- [ ] Documentation and examples

### Phase 4: RL Integration
- [ ] Score export in multiple formats
- [ ] Preference pair generation
- [ ] Integration guides for common RL frameworks
- [ ] Streaming export for large datasets

### Phase 5: Scale & Polish
- [ ] Multi-region deployment
- [ ] Advanced analytics dashboard
- [ ] Grader marketplace
- [ ] Audit and compliance features

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
