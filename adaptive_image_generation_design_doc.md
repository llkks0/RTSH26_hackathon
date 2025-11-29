# Adaptive Image Generation - Design Document

## 1. Overview

This document describes the design for an adaptive image generation system for ad creatives.

The system:

- Runs campaigns per target group (CampaignFlows).
- Iterates through a loop:
  - PromptGen step - generate or refine an image generation prompt and select assets.
  - ImageGen step - generate images for the prompt and attach mocked performance metrics.
  - Analytics step - use an LLM to:
    - Mock Google Ads style analytics (CTR, conversion rate, etc.).
    - Extract differentiation factors between good and bad creatives.
    - Feed those insights into the next PromptGen step.
- Uses embeddings to select relevant assets for each prompt.

Implementation constraints:

- Hackathon level: focus on clear concept and working demo, not full robustness.
- All analytics are mocked via ChatGPT.
- Data is stored in a relational database accessed through a TypeScript ORM (e.g. Prisma, TypeORM, Drizzle).
- Embeddings use a text embedding model (e.g. `text-embedding-3-large`) with text captions for image assets.

---

## 2. Goals and Non-goals

### Goals

- Demonstrate an adaptive loop that improves creatives across a few iterations per target group.
- Show a clear data model for:
  - Campaigns, flows, and steps.
  - Generated images and analytics.
  - LLM prompts and responses.
  - Asset and prompt embeddings.
- Make it easy to visualize:
  - Evolution of prompts and creatives per target group.
  - Differences between high and low performing images.
- Keep the code simple enough to build quickly during a hackathon.

### Non-goals

- Perfect or statistically rigorous optimization.
- Real time or production grade bidding or auction modeling.
- Deep integration with real ad networks.
- Fully accurate multimodal embeddings at pixel level (we approximate via captions for now).

---

## 3. High-level Flow

For each campaign and target group:

1. Initialization
   - Define a Campaign and related TargetGroups and Assets.
   - Create a CampaignFlow per TargetGroup with a base prompt and `maxIterations` (for example 2).

2. PromptGen Step
   - Either:
     - Use a base prompt (iteration 0), or
     - Call LLM with previous analytics and differentiation to refine the prompt.
   - Optionally sample candidate assets using embeddings.
   - Store PromptGen result.

3. ImageGen Step
   - Use the PromptGen result to generate N images.
   - Store GeneratedImage, CampaignImage and link to assets used.
   - Assign preliminary metadata (tags, description) to the images.

4. Analytics Step
   - Call LLM to mock analytics for each CampaignImage:
     - impressions, clicks, conversions, cost.
   - Compute CTR, conversion rate, CPC, CPA in code.
   - Select top and bottom creatives by a chosen goal metric (for example CTR).
   - Call LLM again for differentiation:
     - Human readable explanation.
     - A list of differentiation tags.
     - Recommended best images.
   - Store Analytics result.

5. Iteration
   - If current iteration is less than `maxIterations`, create a new PromptGen step using:
     - Previous prompt.
     - Best creatives.
     - Differentiation tags and text.
   - Repeat steps 3 and 4.

End result: a small chain of steps per target group that illustrates how the system adapts creatives based on performance.

---

## 4. System Components

### 4.1 Backend services

- API Server (TypeScript)
  - Exposes endpoints for:
    - Creating campaigns and flows.
    - Triggering an iteration (PromptGen -> ImageGen -> Analytics).
    - Fetching flow history for visualization.
  - Orchestrates calls to:
    - OpenAI Chat Completions (for PromptGen and Analytics).
    - OpenAI Embeddings (for asset and prompt embeddings).
    - Image generation service (mocked or real).

- LLM Service
  - Wrappers around ChatGPT or GPT-like API:
    - `generatePromptForFlow(...)`
    - `mockAnalyticsForImages(...)`
    - `deriveDifferentiation(...)`
    - `describeAssetForEmbedding(...)` (optional)

- Embedding Service
  - Functions to:
    - Generate text embeddings for:
      - Asset captions (and tags).
      - Prompts.
    - Store and query embeddings (cosine similarity).

### 4.2 Database

- Relational database (for example Postgres).
- ORM in TypeScript (for example Prisma, TypeORM, Drizzle).
- Tables roughly matching the TypeScript data model in section 5.

---

## 5. TypeScript Data Model

The following TypeScript types represent the core domain model and are suitable as a basis for ORM models.

Note: these are conceptual types. For an ORM, you would adapt field types and relations as needed.

```ts
// ---------------------------------------------------------
// Common types
// ---------------------------------------------------------

export type UUID = string;

export type Timestamp = string; // ISO 8601 string

export type StepType = "prompt_gen" | "image_gen" | "analytics";

export type AnalyticsGoalMetric =
  | "ctr"
  | "conversion_rate"
  | "conversions"
  | "cpc"
  | "cpa";

export interface EmbeddingVector {
  // Stored as for example number[] in code, and float[] or separate table in DB
  values: number[];
}
```

---

### 5.1 Assets

```ts
export interface AssetType {
  id: UUID;
  label: string; // for example "background", "product", "model", "logo"
  createdAt: Timestamp;
}

export interface Asset {
  id: UUID;
  name: string;        // for example "Running shoe packshot 1"
  fileName: string;    // path or URL
  assetTypeId: UUID;   // FK -> AssetType.id
  createdAt: Timestamp;
}

// Textual representation of the asset for embeddings
export interface AssetCaption {
  id: UUID;
  assetId: UUID;       // FK -> Asset.id
  caption: string;     // short description for embedding
  tags: string[];      // optional tag list, for example ["running", "shoe", "outdoor"]
  createdAt: Timestamp;
}

// Embedding for assets (text-based for now)
export interface AssetEmbedding {
  id: UUID;
  assetId: UUID;             // FK -> Asset.id
  model: string;             // for example "text-embedding-3-large"
  embedding: EmbeddingVector;
  createdAt: Timestamp;
}
```

---

### 5.2 Target Groups

```ts
export interface TargetGroup {
  id: UUID;
  name: string;          // for example "Berlin - Young Professionals"
  city?: string;
  ageGroup?: string;     // for example "25-35"
  economicStatus?: string; // for example "mid to high income"
  description?: string;  // free text description
  createdAt: Timestamp;
}
```

---

### 5.3 Campaigns and Flows

```ts
export interface Campaign {
  id: UUID;
  name: string;
  basePrompt: string;    // generic prompt template for the campaign
  createdAt: Timestamp;
}

export interface CampaignFlow {
  id: UUID;
  campaignId: UUID;          // FK -> Campaign.id
  targetGroupId: UUID;       // FK -> TargetGroup.id
  initialPrompt: string;     // starting prompt for this flow
  maxIterations: number;     // for example 2 or 3
  createdAt: Timestamp;
}
```

---

### 5.4 Steps and Step Results

#### 5.4.1 CampaignStep

```ts
export interface CampaignStep {
  id: UUID;
  campaignFlowId: UUID;      // FK -> CampaignFlow.id
  stepType: StepType;        // "prompt_gen" | "image_gen" | "analytics"
  orderIndex: number;        // iteration and within-iteration ordering
  inputStepId?: UUID;        // FK -> CampaignStep.id (previous step)
  createdAt: Timestamp;

  // For debugging and analysis of LLM calls
  rawLlmPrompt?: string;     // text sent to LLM (system + user serialized)
  rawLlmResponse?: string;   // raw JSON string or original response
}
```

---

#### 5.4.2 Prompt Generation Result

```ts
export interface PromptGenResult {
  id: UUID;
  stepId: UUID;    // FK -> CampaignStep.id (stepType: "prompt_gen")
  prompt: string;  // final prompt string used for image generation
  notes?: string;  // explanation from LLM, if any
}

// Assets selected for this prompt
export interface PromptGenResultAsset {
  stepId: UUID;    // FK -> CampaignStep.id
  assetId: UUID;   // FK -> Asset.id
}
```

---

#### 5.4.3 Prompt Embeddings (optional but useful)

```ts
export interface PromptEmbedding {
  id: UUID;
  stepId: UUID;           // FK -> CampaignStep.id with stepType "prompt_gen"
  model: string;          // for example "text-embedding-3-large"
  embedding: EmbeddingVector;
  createdAt: Timestamp;
}
```

---

### 5.5 Image Generation

```ts
export interface GeneratedImageMetadata {
  tags?: string[];        // for example ["warm colors", "close-up", "indoor", "person visible"]
  modelVersion?: string;  // image model version identifier
}

export interface GeneratedImage {
  id: UUID;
  fileName: string;                // path or URL of the generated image
  metadata?: GeneratedImageMetadata;
  createdAt: Timestamp;
}

// Link between a generated image and assets that were used to compose it
export interface GeneratedImageAsset {
  generatedImageId: UUID; // FK -> GeneratedImage.id
  assetId: UUID;          // FK -> Asset.id
}
```

---

### 5.6 CampaignImage and Analytics Metrics

CampaignImage represents a generated image as an ad creative within a specific ImageGen step.

```ts
export interface CampaignImage {
  id: UUID;
  stepId: UUID;              // FK -> CampaignStep.id (stepType: "image_gen")
  generatedImageId: UUID;    // FK -> GeneratedImage.id

  // Optional text components for the ad (can be LLM generated)
  headline?: string;
  descriptionLine1?: string;
  descriptionLine2?: string;

  // Prompt that was used to generate this image
  finalPrompt: string;

  // Mocked analytics metrics for this creative
  impressions: number;       // total impressions
  clicks: number;            // total clicks
  conversions: number;       // total conversions
  cost: number;              // total cost in campaign currency

  // Derived metrics for convenience
  ctr: number;               // clicks / impressions
  conversionRate: number;    // conversions / clicks
  cpc: number;               // cost / clicks
  cpa: number;               // cost / conversions

  createdAt: Timestamp;
}
```

---

### 5.7 Analytics Results

```ts
export interface AnalyticsResult {
  id: UUID;
  stepId: UUID;                // FK -> CampaignStep.id (stepType: "analytics")
  goalMetric: AnalyticsGoalMetric; // for example "ctr" or "conversions"

  // LLM derived explanation and tags
  differentiationText: string; // human readable explanation from LLM
  differentiationTags: string[]; // concise tags describing what works

  createdAt: Timestamp;
}

// Best images for a given analytics result
export interface AnalyticsBestImage {
  analyticsResultId: UUID; // FK -> AnalyticsResult.id
  campaignImageId: UUID;   // FK -> CampaignImage.id
  rank: number;            // 1, 2, 3...
}
```

---

## 6. LLM Flows (Prompts at a Glance)

### 6.1 Asset Captioning (one time per asset)

Goal: produce a text caption and tags for each asset to allow text embeddings.

Input:

- Context about the brand or campaign (optional).
- Rough description of the asset, or the asset name.
- If you have a human description, you can skip LLM here.

Output:

- AssetCaption.caption
- AssetCaption.tags

---

### 6.2 PromptGen LLM Call

Input:
  - Target group info.
  - Previous prompt (if any).
  - Best creatives and their differentiation tags (from previous iteration).

Output:
  - New prompt string.
  - Optional notes describing the changes.

Result goes into PromptGenResult.

---

### 6.3 Analytics Mock LLM Call

Input:
  - Target group info.
  - List of creatives with:
    - prompts
    - tags
  - Goal: assign realistic performance numbers.

Output:
  - For each creative id:
    - impressions
    - clicks
    - conversions
    - cost

Numbers are stored on CampaignImage, derived metrics computed in code.

---

### 6.4 Differentiation LLM Call

Input:
  - Target group info.
  - List of top and bottom creatives with their prompts, tags, and metrics.
  - Goal metric (for example "ctr").

Output:
  - differentiationText
  - differentiationTags
  - bestCreativeIds (for AnalyticsBestImage)

---

## 7. Embedding Usage

- Asset embeddings
  - AssetCaption.caption + tags are embedded via text embedding model.
  - Stored in AssetEmbedding.

- Prompt embeddings
  - Each PromptGen step (or each prompt string) is embedded.
  - Stored in PromptEmbedding.

- Asset selection for ImageGen
  - Given a new prompt:
    - Find its embedding.
    - Compute cosine similarity against AssetEmbedding.
    - Select top K assets.
  - These assets can be:
    - Used directly in composing the generation prompt.
    - Or shown in the UI as "recommended creative ingredients".

---

## 8. Example Minimal Flow

1. Create:
   - Campaign "Running Shoes Launch".
   - TargetGroup "Berlin - Young Professionals".
   - Several Assets with captions and embeddings.

2. CampaignFlow:
   - initialPrompt: "Generate lifestyle images of young professionals in Berlin using modern running shoes in daily life."

3. Iteration 0:
   - CampaignStep 0 - PromptGen:
     - PromptGenResult.prompt = initialPrompt.
   - CampaignStep 1 - ImageGen:
     - Generate 4 images.
     - Store GeneratedImage, CampaignImage.
     - Call analytics mock LLM, update metrics.
   - CampaignStep 2 - Analytics:
     - Call differentiation LLM.
     - Store AnalyticsResult and AnalyticsBestImage.

4. Iteration 1:
   - CampaignStep 3 - PromptGen:
     - LLM refines prompt based on differentiation:
       - For example "More warm colors, visible city context, person in motion."
   - CampaignStep 4 - ImageGen:
     - Generate 4 new images based on updated prompt.
     - Mock analytics again.
   - CampaignStep 5 - Analytics:
     - New differentiation.

5. Stop after 2 iterations. UI can now show:

- How prompts evolved.
- How metrics changed.
- How differentiation tags evolved.

---

## 9. Future Extensions

- Replace text-only embeddings with true multimodal embeddings (images and text in a shared space).
- Add manual override to let a user mark a creative as "best" regardless of metrics.
- Support multiple objectives and tradeoffs (for example CTR vs CPA).
- Introduce simple A or B test scheduling over time.
- Log more LLM metadata (tokens, latency, cost) for real world analysis.
