# 第八章：混合搜索深度解析（Hybrid Search Deep Dive）

> 本章对 `core/search/` 目录下各模块做技术深度解析，涵盖向量搜索、关键词搜索、RRF 融合、去重策略、搜索增强和参数调优。

---

## 8.1 向量搜索（Vector Search）

### 8.1.1 核心原理

向量搜索的本质是在高维向量空间中寻找与查询向量最接近的 k 个 Chunk。

GBrain 使用 **cosine similarity**（余弦相似度）作为距离度量：

```
cosine(a, b) = (a · b) / (|a| × |b|)
```

取值范围 `[-1, 1]`，值越大表示越相似。在 RRF 管线中实际使用的是 `cosine_distance = 1 - cosine(a, b)`（距离越小越接近）。

### 8.1.2 pgvector 集成

PostgreSQL 通过 `pgvector` 扩展支持向量操作。GBrain 在 schema 中定义了 1536 维的向量列：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
ALTER TABLE content_chunks ADD COLUMN embedding vector(1536);
```

查询时使用 `<=>` 操作符：

```sql
SELECT *, embedding <=> $1 AS distance
FROM content_chunks
ORDER BY embedding <=> $1
LIMIT $2;
```

### 8.1.3 Embedding 生成

使用 OpenAI `text-embedding-3-large` 模型：

```typescript
// core/embedding.ts
const EMBEDDING_MODEL = 'text-embedding-3-large';
const EMBEDDING_DIMENSIONS = 1536;

export async function embed(text: string): Promise<Float32Array> {
  // 超过 8000 字符截断
  const truncated = text.slice(0, 8000);
  const response = await openai.embeddings.create({
    model: EMBEDDING_MODEL,
    input: truncated,
  });
  return new Float32Array(response.data[0].embedding);
}
```

重试策略：
- 指数退避：4s base，120s cap，最多 5 次
- 429 时优先尊重 `Retry-After` header
- 批量大小：100 条/请求

### 8.1.4 向量搜索的语义盲区

向量搜索并非万能，存在以下局限：

| 问题 | 描述 | 示例 |
|------|------|------|
| **语义漂移** | 相近向量可能语义无关 | 「苹果股价」和「苹果公司」向量接近，但上下文不同 |
| **精确关键词缺失** | 罕见专业术语、缩写可能被误解 | 「GBrain」可能被理解为未知词丢弃 |
| **数字敏感度低** | 版本号、日期等精确信息难以捕捉 | 「v0.20.0」和「v0.19.0」向量几乎相同 |

这正是需要融合关键词搜索的原因。

---

## 8.2 关键词搜索（Keyword Search）

### 8.2.1 pg_trgm 扩展

GBrain 使用 PostgreSQL 的 `pg_trgm` 扩展实现 trigram（三元组）模糊匹配。trigram 将字符串切分为连续 3 个字符的滑动窗口：

```
"rust" → {" ru", "rus", "ust", "st "}
```

### 8.2.2 搜索机制

```sql
-- 启用 trigram 索引
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX ON content_chunks USING gin (chunk_text gin_trgm_ops);

-- 搜索：ILIKE 支持大小写不敏感，%query% 做子串匹配
SELECT *, similarity(chunk_text, $1) AS sim
FROM content_chunks
WHERE chunk_text ILIKE '%' || $1 || '%'
   OR slug ILIKE '%' || $1 || '%'
ORDER BY sim DESC;
```

相比 `LIKE %query%`，trigram 的优势：
- 支持拼写错误容错（Levenshtein distance）
- 利用 GIN 索引加速
- 返回相似度得分（0~1）

### 8.2.3 BM25 算法

pg_trgm 相似度是简单的字符匹配，BM25（Best Matching 25）是更成熟的文档排名算法。

PostgreSQL 的 `ts_rank()` 和 `ts_rank_cd()` 函数实现了 BM25 的变体，用于全文搜索：

```sql
SELECT *,
  ts_rank(to_tsvector('english', chunk_text), query) AS rank
FROM content_chunks, plainto_tsquery('english', $1) AS query
WHERE to_tsvector('english', chunk_text) @@ query
ORDER BY rank DESC;
```

GBrain 的关键词搜索通常同时使用 trigram 模糊匹配 + tsvector 全文搜索，然后对两个排名列表做并集。

### 8.2.4 `keyword.ts` 实现

```typescript
// search/keyword.ts
export async function keywordSearch(
  engine: BrainEngine,
  query: string,
  opts?: SearchOpts,
): Promise<SearchResult[]> {
  return engine.searchKeyword(query, opts);
}
```

实际 SQL 编排由 `postgres-engine.ts` / `pglite-engine.ts` 的 `searchKeyword()` 方法实现，包含：
- `pg_trgm` trigram 相似度搜索
- `tsvector` 全文搜索
- 来源 Boost（`source-boost.ts` 注入的 CASE WHEN）
- 硬排除（`test/`, `archive/` 等）

---

## 8.3 RRF 融合算法

### 8.3.1 公式

**Reciprocal Rank Fusion**（倒数排名融合）将多个排名列表合并为一个：

```
RRF_score(d) = Σ 1 / (k + rank_i(d))
```

- `d`：文档（Chunk）
- `k`：平滑参数（通常 k = 60）
- `rank_i(d)`：文档 d 在第 i 个排名列表中的排名（从 0 开始）

### 8.3.2 为什么用 RRF 而不是加权平均？

假设关键词搜索和向量搜索各返回 Top 10，如果用简单的加权平均：

```typescript
// ❌ 加权平均的问题
const blended = 0.5 * keywordScore + 0.5 * vectorScore;
```

问题在于：
1. **不同引擎得分分布不同**：关键词的 BM25 分数和向量的 cosine similarity 量纲完全不同
2. **排名比分数更可靠**：第一名和第二名的差距可能远大于 0.01 分差
3. **无法跨列表比较**：第 3 名的关键词结果和第 100 名的向量结果无法直接对比分数

RRF 只依赖排名，不依赖分数绝对值天然解决了这些问题。

### 8.3.3 k 参数的作用

```
k = 60 时：
- rank=0（第1名）→ 1/(60+0) = 0.0167
- rank=1（第2名）→ 1/(60+1) = 0.0164
- rank=59（第60名）→ 1/(60+59) = 0.0084
- rank=100 → 1/160 = 0.00625
```

k 值越大，RRF 对排名的敏感度越低（不同排名之间的差距被压缩）。GBrain 默认 k=60，经过调优适合知识库搜索场景。

### 8.3.4 RRF 示意图

```{mermaid}
flowchart LR
    KW1["关键词 #1<br/>Chunk A"]
    KW2["关键词 #2<br/>Chunk B"]
    KW3["关键词 #3<br/>Chunk C"]
    KW4["关键词 #4<br/>Chunk D"]

    Vec1["向量 #1<br/>Chunk A"]
    Vec2["向量 #2<br/>Chunk E"]
    Vec3["向量 #3<br/>Chunk B"]
    Vec4["向量 #4<br/>Chunk F"]

    RRF["RRF 融合<br/>k=60"]
    Final["最终排名"]

    KW1 & KW2 & KW3 & KW4 --> RRF
    Vec1 & Vec2 & Vec3 & Vec4 --> RRF

    RRF --> Final

    style RRF fill:#fff3e0
```

### 8.3.5 `rrfFusion()` 实现

```typescript
// search/hybrid.ts
export function rrfFusion(lists: SearchResult[][], k: number, applyBoost = true): SearchResult[] {
  const scores = new Map<string, { result: SearchResult; score: number }>();

  for (const list of lists) {
    for (let rank = 0; rank < list.length; rank++) {
      const r = list[rank];
      const key = `${r.slug}:${r.chunk_id ?? r.chunk_text.slice(0, 50)}`;
      const rrfScore = 1 / (k + rank);  // ← 倒数排名

      if (existing) {
        existing.score += rrfScore;    // 累加跨列表得分
      } else {
        scores.set(key, { result: r, score: rrfScore });
      }
    }
  }

  // 归一化到 0-1 + compiled_truth boost
  const maxScore = Math.max(...entries.map(e => e.score));
  for (const e of entries) {
    e.score = e.score / maxScore;
    if (applyBoost && e.result.chunk_source === 'compiled_truth') {
      e.score *= COMPILED_TRUTH_BOOST; // 2.0x
    }
  }

  return entries.sort((a, b) => b.score - a.score).map(({ result, score }) => ({ ...result, score }));
}
```

---

## 8.4 结果去重（Deduplication）

去重是混合搜索管线的关键一环——既要把重复内容去掉，又不能丢失重要信息（如 compiled_truth 保障）。

### 8.4.1 四层去重策略

`dedup.ts` 实现了 4 层过滤：

```{mermaid}
flowchart TD
    Input["原始结果"]
    L1["Layer 1<br/>dedupBySource<br/>每页保留 Top3 Chunk"]
    L2["Layer 2<br/>dedupByTextSimilarity<br/>Jaccard > 0.85 → 去除"]
    L3["Layer 3<br/>enforceTypeDiversity<br/>同类型不超过 60%"]
    L4["Layer 4<br/>capPerPage<br/>每页最多 2 个 Chunk"]
    GT["Guarantee<br/>compiled_truth 保障"]
    Output["最终结果"]

    Input --> L1 --> L2 --> L3 --> L4 --> GT --> Output

    style L1 fill:#e8f5e9
    style L4 fill:#fff3e0
    style GT fill:#fce4ec
```

### 8.4.2 各层详解

**Layer 1 - 按来源分页（`dedupBySource`）**

```typescript
function dedupBySource(results: SearchResult[]): SearchResult[] {
  const byPage = new Map<string, SearchResult[]>();
  for (const r of results) {
    byPage.getOrCreate(pageKey(r), []).push(r);
  }
  return Array.from(byPage.values())
    .flatMap(chunks => chunks.sort((a,b) => b.score - a.score).slice(0, 3));
}
```

每页（source_id + slug 组合键）最多保留 3 个最高分 Chunk。

**Layer 2 - 文本相似度（`dedupByTextSimilarity`）**

使用 Jaccard 相似度（词集合交集/并集）作为 cosine similarity 的近似：

```typescript
function jaccard(a: Set<string>, b: Set<string>): number {
  const intersection = new Set([...a].filter(w => b.has(w))).size;
  const union = new Set([...a, ...b]).size;
  return intersection / union;
}
// Jaccard > 0.85 → 认为是重复
```

**Layer 3 - 类型多样性（`enforceTypeDiversity`）**

防止结果被同一页面类型（如 `fenced_code`）占满。任何单一类型不超过总结果的 60%。

**Layer 4 - 每页上限（`capPerPage`）**

默认每页最多 2 个 Chunk。两遍检索时放宽到 `min(10, walkDepth × 5)`。

### 8.4.3 复合页面键

v0.18.0 引入多源支持后，页面键改为复合键 `(source_id, slug)`：

```typescript
function pageKey(r: SearchResult): string {
  const source = r.source_id ?? 'default';
  return `${source}:${r.slug}`;
}
```

避免不同源下相同 slug 的页面被错误合并。

### 8.4.4 Compiled Truth 保障

这是去重管线的最后一道保险：

```typescript
function guaranteeCompiledTruth(results: SearchResult[], preDedup: SearchResult[]): SearchResult[] {
  for (const [key, pageChunks] of byPage) {
    const hasCompiledTruth = pageChunks.some(c => c.chunk_source === 'compiled_truth');
    if (!hasCompiledTruth) {
      // 从 pre-dedup 中找回该页最好的 compiled_truth Chunk
      const candidate = preDedup
        .filter(r => pageKey(r) === key && r.chunk_source === 'compiled_truth')
        .sort((a, b) => b.score - a.score)[0];
      if (candidate) {
        // 替换该页得分最低的 Chunk
        const lowestIdx = output.findIndex(r => pageKey(r) === key && r.score === minScore);
        output[lowestIdx] = candidate;
      }
    }
  }
}
```

---

## 8.5 搜索增强（Search Enrichment）

### 8.5.1 Resolver 系统概述

GBrain 的 Resolver 系统为搜索结果提供「外部数据补充」能力。当搜索命中文档中的外部引用（如 Twitter 句柄、URL），Resolver 自动补全最新信息。

```{mermaid}
flowchart LR
    SearchResult["搜索结果<br/>含外部引用"]
    Resolver["ResolverRegistry"]
    URL["URL Reachable<br/>检查链接是否有效"]
    XAPI["X API<br/>查找推文"]
    Brain["Brain Local<br/>脑内slug查找"]
    Enriched["富化后的结果"]

    SearchResult --> Resolver
    Resolver --> URL
    Resolver --> XAPI
    Resolver --> Brain
    URL & XAPI & Brain --> Enriched
```

### 8.5.2 Resolver 接口设计

每个 Resolver 实现统一的接口（`core/resolvers/interface.ts`）：

```typescript
export interface Resolver<I, O> {
  readonly id: string;           // slug-cased, e.g. "x_handle_to_tweet"
  readonly cost: ResolverCost;   // 'free' | 'rate-limited' | 'paid'
  readonly backend: string;       // "x-api-v2", "brain-local", "head-check"

  // 判断 resolver 是否可用（检查 env、API key 等）
  available(ctx: ResolverContext): Promise<boolean>;

  // 核心解析方法
  resolve(req: ResolverRequest<I>): Promise<ResolverResult<O>>;
}

export interface ResolverResult<O> {
  value: O;
  confidence: number;    // 0.0-1.0，1.0=确定性结果
  source: string;       // "x-api-v2"
  fetchedAt: Date;
  costEstimate?: number;
  raw?: unknown;        // 保留原始响应
}
```

### 8.5.3 内置 Resolver 示例

**URL Reachable**（`builtin/url-reachable.ts`）

```typescript
const urlReachable: Resolver<string, boolean> = {
  id: 'url_reachable',
  cost: 'free',
  backend: 'head-check',
  async available() { return true; },
  async resolve({ input }) {
    const response = await fetch(input, { method: 'HEAD', timeout: 5000 });
    return {
      value: response.ok,
      confidence: 1.0,
      source: 'head-check',
      fetchedAt: new Date(),
    };
  },
};
```

**X (Twitter) Handle 查找**（`builtin/x-api/handle-to-tweet.ts`）

查找特定 X 句柄的最新推文，用于补充人物页面的社交媒体信息。

### 8.5.4 Resolver 注册

```typescript
// core/resolvers/registry.ts
class ResolverRegistry {
  private resolvers = new Map<string, Resolver<any, any>>();

  register<I, O>(resolver: Resolver<I, O>): void {
    this.resolvers.set(resolver.id, resolver);
  }

  async resolve<I, O>(
    id: string,
    input: I,
    ctx: ResolverContext,
  ): Promise<ResolverResult<O>> {
    const resolver = this.resolvers.get(id);
    if (!resolver) throw new ResolverError('not_found', `Unknown resolver: ${id}`);
    if (!(await resolver.available(ctx))) {
      throw new ResolverError('unavailable', `Resolver ${id} is unavailable`);
    }
    return resolver.resolve({ input, context: ctx });
  }
}
```

---

## 8.6 搜索参数调优

### 8.6.1 核心参数一览

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `limit` | 20 | 返回结果上限 |
| `offset` | 0 | 分页偏移 |
| `detail` | auto | `'low'`编译真相 / `'medium'`全部 / `'high'`时间线优先 |
| `expansion` | true | 是否启用查询扩展 |
| `rrfK` | 60 | RRF 平滑参数，越大排名差异越被压缩 |
| `walkDepth` | 0 | 两遍检索跳数，0=关闭，1-2=启用 |
| `nearSymbol` | - | 符号名锚点，直接定位到代码定义 |

### 8.6.2 Dedup 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `cosineThreshold` | 0.85 | Jaccard 相似度阈值，超过视为重复 |
| `maxTypeRatio` | 0.6 | 单一类型最大占比 |
| `maxPerPage` | 2 | 每页最大 Chunk 数 |

### 8.6.3 场景化建议

**日常笔记搜索**

```typescript
hybridSearch(engine, query, {
  detail: 'medium',    // 默认
  expansion: true,     // 启用同义扩展
  walkDepth: 0,        // 不需要代码感知
});
```

**代码定位（使用两遍检索）**

```typescript
hybridSearch(engine, query, {
  detail: 'medium',
  walkDepth: 2,                    // 开启两遍检索
  nearSymbol: 'BrainEngine.searchKeyword',  // 锚定符号
  symbolKind: 'function',          // 只看函数
  language: 'typescript',
});
```

**实体查询（who is / what is）**

```typescript
hybridSearch(engine, query, {
  detail: 'low',        // 只要 compiled_truth
  expansion: false,    // 短查询不需要扩展
});
```

**时间线查询（when / history）**

```typescript
hybridSearch(engine, query, {
  detail: 'high',      // 需要 timeline chunk 全文
  rrfK: 60,            // 默认即可
});
```

### 8.6.4 两遍检索流程图

```{mermaid}
flowchart TB
    Q["查询: useState hook"]

    subgraph P1["== 第一遍：锚点检索 =="]
        K1["关键词搜索 Top N"]
        V1["向量搜索 Top N"]
        Merge["RRF 融合"]
        Anchor["锚点集: Top 10 Chunks"]
        K1 & V1 --> Merge --> Anchor
    end

    subgraph P2["== 第二遍：图扩展 =="]
        Walk["沿 code_edges 遍历"]
        CE1["code_edges_chunk: to_chunk_id"]
        CE2["code_edges_symbol: 符号反向查找"]
        Neighbor["结构邻居: score × 1/(1+hop)"]
        Merge2["与锚点集合并，按 score 排序"]
        Walk --> CE1 --> Neighbor
        Walk --> CE2 --> Neighbor
        Merge2 --> Neighbor
    end

    subgraph P3["== 去重 =="]
        Dedup["四层去重 + compiled_truth 保障"]
    end

    P1 --> Anchor --> Walk --> P2 --> Dedup --> P3

    style Q fill:#e3f2fd
    style Anchor fill:#e1f5fe
    style Walk fill:#fff3e0
    style Dedup fill:#f3e5f5
```

---

## 本章小结

GBrain 的混合搜索管线精心平衡了多种检索策略：

| 模块 | 技术基础 | 解决的问题 |
|------|---------|-----------|
| 向量搜索 | text-embedding-3-large + pgvector | 语义相似召回 |
| 关键词搜索 | pg_trgm trigram + BM25/tsvector | 精确关键词匹配 |
| RRF 融合 | 倒数排名融合（k=60） | 多引擎排名合并 |
| 余弦重打分 | cosine similarity re-blend | 语义精细调整 |
| 反链增强 | `log(1 + backlink_count)` | 权威性信号 |
| 来源 Boost | slug 前缀权重 | 内容质量先验 |
| 去重 | 4层过滤 + compiled_truth保障 | 结果多样性 |
| 两遍检索 | 代码调用图遍历 | 代码结构感知 |

这套管线的设计哲学是**互补优于单一**：每个搜索引擎都有盲区，通过多引擎融合 + 多阶段增强，最大化各类查询的成功率。
